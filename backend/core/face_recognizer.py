"""
Face Recognition Engine using insightface
Loads existing face database and performs recognition
"""
import pickle
import numpy as np
import insightface
import time
from insightface.app import FaceAnalysis
from typing import List, Tuple, Dict, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FaceDetection:
    """Face detection result"""
    bbox: np.ndarray  # [x1, y1, x2, y2]
    embedding: np.ndarray  # 512-dim feature vector
    confidence: float  # Detection confidence
    landmarks: Optional[np.ndarray] = None


@dataclass
class RecognitionResult:
    """Face recognition result"""
    bbox: np.ndarray
    embedding: np.ndarray
    confidence: float
    person_id: Optional[str] = None
    person_name: Optional[str] = None
    similarity: float = 0.0
    is_known: bool = False


class FaceRecognizer:
    """Face recognition engine with insightface"""
    
    def __init__(self, database_path: str, similarity_threshold: float = 0.42,
                 gpu_id: int = 0, det_size: Tuple[int, int] = (640, 640),
                 grace_period: float = 10.0, model_name: str = "buffalo_s",
                 enter_threshold: float = 0.42, stay_threshold: float = 0.42,
                 known_embedding_history: int = 1, use_hysteresis: bool = False):
        """
        Initialize face recognizer

        Args:
            database_path: Path to face database pickle file
            similarity_threshold: Cosine similarity threshold for matching (backward compatibility)
            gpu_id: GPU device ID (-1 for CPU)
            det_size: Detection input size
            grace_period: Grace period (seconds) for recently seen known persons (default: 10s)
            model_name: Model name (buffalo_s or buffalo_l)
            enter_threshold: Threshold for initial recognition (hysteresis)
            stay_threshold: Threshold for maintaining recognition (hysteresis)
            known_embedding_history: Number of embeddings to keep for centroid calculation
            use_hysteresis: Whether to use hysteresis logic
        """
        self.similarity_threshold = similarity_threshold
        self.model_name = model_name
        self.database_path = database_path
        self.grace_period = grace_period
        self.known_faces = {}  # person_id -> {'name': str, 'embeddings': [np.ndarray]}

        # Hysteresis parameters
        self.enter_threshold = enter_threshold
        self.stay_threshold = stay_threshold
        self.known_embedding_history = known_embedding_history
        self.use_hysteresis = use_hysteresis

        # Track recently seen known persons to prevent false unknown alerts
        # Format: {person_id: {'embeddings': [np.ndarray], 'centroid': np.ndarray,
        #                      'timestamp': float, 'name': str, 'currently_known': bool}}
        self.recent_known_cache: Dict[str, dict] = {}
        
        # Initialize insightface with GPU acceleration
        logger.info(f"Initializing insightface with GPU {gpu_id}")
        
        # Force CUDA provider for GPU acceleration with optimizations
        if gpu_id >= 0:
            providers = [
                ('CUDAExecutionProvider', {
                    'device_id': gpu_id,
                    'arena_extend_strategy': 'kSameAsRequested',  # Changed from kNextPowerOfTwo
                    'gpu_mem_limit': 6 * 1024 * 1024 * 1024,  # Increased to 6GB
                    'cudnn_conv_algo_search': 'EXHAUSTIVE',
                    'do_copy_in_default_stream': True,
                    'cudnn_conv_use_max_workspace': '1',  # OPTIMIZATION: Use max workspace
                    'cudnn_conv1d_pad_to_nc1d': '1',  # OPTIMIZATION: Pad for better performance
                }),
                'CPUExecutionProvider'
            ]
        else:
            providers = ['CPUExecutionProvider']
        
        self.app = FaceAnalysis(
            name=self.model_name,
            providers=providers
        )
        self.app.prepare(ctx_id=gpu_id, det_size=det_size)
        
        logger.info(f"InsightFace initialized with providers: {[p if isinstance(p, str) else p[0] for p in providers]}")
        logger.info(f"🚀 Model: {self.model_name}")
        if gpu_id >= 0:
            logger.info("⚡ cuDNN optimizations ENABLED - Max workspace + EXHAUSTIVE search")
        
        # Load face database
        self.load_database()
        
        logger.info(f"FaceRecognizer initialized with {len(self.known_faces)} known persons")
    
    def load_database(self):
        """Load face database from pickle file"""
        try:
            with open(self.database_path, 'rb') as f:
                self.known_faces = pickle.load(f)
            
            # Validate database structure
            total_embeddings = sum(len(data['embeddings']) for data in self.known_faces.values())
            logger.info(f"Loaded {len(self.known_faces)} persons with {total_embeddings} embeddings")
            
            # Log sample persons
            sample_persons = list(self.known_faces.items())[:3]
            for person_id, data in sample_persons:
                logger.info(f"  - {person_id}: {data['name']} ({len(data['embeddings'])} embeddings)")
                
        except FileNotFoundError:
            logger.error(f"Face database not found at {self.database_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading face database: {e}")
            raise

    def _update_known_embedding_centroid(self, person_id: str, new_embedding: np.ndarray):
        """
        Update known person's embedding centroid with moving average

        Args:
            person_id: Person identifier
            new_embedding: New embedding to add to history
        """
        if person_id not in self.recent_known_cache:
            # Initialize if not exists
            self.recent_known_cache[person_id] = {
                'embeddings': [],
                'centroid': new_embedding.copy(),
                'timestamp': time.time(),
                'name': '',
                'currently_known': False
            }

        cache_entry = self.recent_known_cache[person_id]

        # Add new embedding to history
        cache_entry['embeddings'].append(new_embedding.copy())

        # Keep only last N embeddings
        if len(cache_entry['embeddings']) > self.known_embedding_history:
            cache_entry['embeddings'].pop(0)

        # Update centroid as average of history
        cache_entry['centroid'] = np.mean(cache_entry['embeddings'], axis=0)

        # Re-normalize centroid
        cache_entry['centroid'] = cache_entry['centroid'] / np.linalg.norm(cache_entry['centroid'])

    def detect_faces(self, frame: np.ndarray) -> List[FaceDetection]:
        """
        Detect faces in frame and extract embeddings
        
        Args:
            frame: Input image (BGR format)
            
        Returns:
            List of FaceDetection objects
        """
        try:
            # Detect faces
            faces = self.app.get(frame)
            
            detections = []
            for face in faces:
                # Handle different embedding formats
                try:
                    embedding = face.normed_embedding
                except (AttributeError, IndexError):
                    # Fallback to embedding field if normed_embedding doesn't exist
                    if hasattr(face, 'embedding'):
                        embedding = face.embedding
                        # Normalize it manually
                        embedding = embedding / np.linalg.norm(embedding)
                    else:
                        logger.warning("Face object has no embedding, skipping")
                        continue
                
                detection = FaceDetection(
                    bbox=face.bbox.astype(int),
                    embedding=embedding,
                    confidence=float(face.det_score),
                    landmarks=face.landmark_2d_106 if hasattr(face, 'landmark_2d_106') else None
                )
                detections.append(detection)
            
            return detections
            
        except Exception as e:
            logger.error(f"Error detecting faces: {e}", exc_info=True)
            return []
    
    def recognize_face(self, embedding: np.ndarray) -> Tuple[Optional[str], Optional[str], float]:
        """
        Recognize a face by comparing embedding with database
        Includes hysteresis for known person continuity and grace period for temporary occlusions

        Args:
            embedding: Face embedding (512-dim)

        Returns:
            Tuple of (person_id, person_name, similarity_score)
        """
        if not self.known_faces:
            return None, None, 0.0

        current_time = time.time()

        # FIRST: Check recently seen known persons (grace period logic)
        # This prevents known persons from being marked as unknown during temporary occlusions
        for person_id, cache_data in list(self.recent_known_cache.items()):
            time_since_seen = current_time - cache_data['timestamp']

            # Remove expired entries
            if time_since_seen > self.grace_period:
                del self.recent_known_cache[person_id]
                continue

            # Use centroid if hysteresis enabled, otherwise use single embedding
            reference_embedding = (cache_data['centroid'] if self.use_hysteresis and 'centroid' in cache_data
                                 else cache_data.get('embedding', cache_data.get('centroid', embedding)))

            similarity = np.dot(embedding, reference_embedding) / (
                np.linalg.norm(embedding) * np.linalg.norm(reference_embedding)
            )

            # Relaxed threshold for grace period (always use 0.30)
            if similarity >= 0.30:
                # Update cache with new embedding and centroid
                if self.use_hysteresis:
                    self._update_known_embedding_centroid(person_id, embedding)
                    cache_entry = self.recent_known_cache[person_id]
                    cache_entry['timestamp'] = current_time
                    cache_entry['name'] = cache_data['name']
                    cache_entry['currently_known'] = True
                else:
                    # Original single embedding behavior
                    self.recent_known_cache[person_id] = {
                        'embedding': embedding.copy(),
                        'timestamp': current_time,
                        'name': cache_data['name'],
                        'currently_known': True
                    }

                logger.debug(f"Grace period match: {person_id} (similarity={similarity:.3f}, "
                           f"time_since_seen={time_since_seen:.1f}s)")
                return person_id, cache_data['name'], float(similarity)

        # SECOND: Check against full database with hysteresis or single threshold
        best_match_id = None
        best_match_name = None
        best_similarity = 0.0
        best_person_data = None

        # Compare with all known faces
        for person_id, data in self.known_faces.items():
            for known_embedding in data['embeddings']:
                # Cosine similarity
                similarity = np.dot(embedding, known_embedding) / (
                    np.linalg.norm(embedding) * np.linalg.norm(known_embedding)
                )

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match_id = person_id
                    best_match_name = data['name']
                    best_person_data = data

        # Apply hysteresis or single threshold logic
        is_recognized = False

        if self.use_hysteresis:
            # HYSTERESIS LOGIC: Check if this person is already in cache (currently known)
            if best_match_id in self.recent_known_cache:
                cache_entry = self.recent_known_cache[best_match_id]
                currently_known = cache_entry.get('currently_known', False)

                if currently_known:
                    # STAY threshold: more lenient for maintaining recognition
                    is_recognized = (best_similarity >= self.stay_threshold)
                else:
                    # ENTER threshold: stricter for initial recognition
                    is_recognized = (best_similarity >= self.enter_threshold)
            else:
                # No cache entry - use ENTER threshold for new recognition
                is_recognized = (best_similarity >= self.enter_threshold)
        else:
            # SINGLE THRESHOLD (original behavior)
            is_recognized = (best_similarity >= self.similarity_threshold)

        if is_recognized:
            # Update cache with embedding and centroid
            if self.use_hysteresis:
                self._update_known_embedding_centroid(best_match_id, embedding)
                cache_entry = self.recent_known_cache[best_match_id]
                cache_entry['timestamp'] = current_time
                cache_entry['name'] = best_match_name
                cache_entry['currently_known'] = True
            else:
                # Original single embedding behavior
                self.recent_known_cache[best_match_id] = {
                    'embedding': embedding.copy(),
                    'timestamp': current_time,
                    'name': best_match_name,
                    'currently_known': True
                }

            return best_match_id, best_match_name, float(best_similarity)

        return None, None, float(best_similarity)
    
    def process_frame(self, frame: np.ndarray) -> List[RecognitionResult]:
        """
        Detect and recognize all faces in a frame
        
        Args:
            frame: Input image (BGR format)
            
        Returns:
            List of RecognitionResult objects
        """
        detections = self.detect_faces(frame)
        results = []
        
        for detection in detections:
            person_id, person_name, similarity = self.recognize_face(detection.embedding)
            
            result = RecognitionResult(
                bbox=detection.bbox,
                embedding=detection.embedding,
                confidence=detection.confidence,
                person_id=person_id,
                person_name=person_name,
                similarity=similarity,
                is_known=(person_id is not None)
            )
            results.append(result)
        
        return results
    
    def get_model_info(self) -> Dict:
        """Get model information for display"""
        return {
            "model_name": f"insightface {self.model_name}",
            "detector": "RetinaFace",
            "recognizer": "ArcFace",
            "embedding_dim": 512,
            "similarity_threshold": self.similarity_threshold,
            "known_persons": len(self.known_faces)
        }

