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
                 grace_period: float = 10.0):
        """
        Initialize face recognizer
        
        Args:
            database_path: Path to face database pickle file
            similarity_threshold: Cosine similarity threshold for matching
            gpu_id: GPU device ID (-1 for CPU)
            det_size: Detection input size
            grace_period: Grace period (seconds) for recently seen known persons (default: 10s)
        """
        self.similarity_threshold = similarity_threshold
        self.database_path = database_path
        self.grace_period = grace_period
        self.known_faces = {}  # person_id -> {'name': str, 'embeddings': [np.ndarray]}
        
        # Track recently seen known persons to prevent false unknown alerts
        # Format: {person_id: {'embedding': np.ndarray, 'timestamp': float, 'name': str}}
        self.recent_known_cache: Dict[str, dict] = {}
        
        # Initialize insightface with GPU acceleration
        logger.info(f"Initializing insightface with GPU {gpu_id}")
        
        # Force CUDA provider for GPU acceleration
        if gpu_id >= 0:
            providers = [
                ('CUDAExecutionProvider', {
                    'device_id': gpu_id,
                    'arena_extend_strategy': 'kNextPowerOfTwo',
                    'gpu_mem_limit': 4 * 1024 * 1024 * 1024,  # 4GB
                    'cudnn_conv_algo_search': 'EXHAUSTIVE',
                    'do_copy_in_default_stream': True,
                }),
                'CPUExecutionProvider'
            ]
        else:
            providers = ['CPUExecutionProvider']
        
        self.app = FaceAnalysis(
            name='buffalo_l',
            providers=providers
        )
        self.app.prepare(ctx_id=gpu_id, det_size=det_size)
        
        logger.info(f"InsightFace initialized with providers: {[p if isinstance(p, str) else p[0] for p in providers]}")
        
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
                detection = FaceDetection(
                    bbox=face.bbox.astype(int),
                    embedding=face.normed_embedding,
                    confidence=float(face.det_score),
                    landmarks=face.landmark_2d_106 if hasattr(face, 'landmark_2d_106') else None
                )
                detections.append(detection)
            
            return detections
            
        except Exception as e:
            logger.error(f"Error detecting faces: {e}")
            return []
    
    def recognize_face(self, embedding: np.ndarray) -> Tuple[Optional[str], Optional[str], float]:
        """
        Recognize a face by comparing embedding with database
        Includes grace period for recently seen known persons to handle temporary occlusions
        
        Args:
            embedding: Face embedding (512-dim)
            
        Returns:
            Tuple of (person_id, person_name, similarity_score)
        """
        if not self.known_faces:
            return None, None, 0.0
        
        current_time = time.time()
        
        # FIRST: Check recently seen known persons with relaxed threshold
        # This prevents known persons from being marked as unknown during temporary occlusions
        for person_id, cache_data in list(self.recent_known_cache.items()):
            time_since_seen = current_time - cache_data['timestamp']
            
            # Remove expired entries
            if time_since_seen > self.grace_period:
                del self.recent_known_cache[person_id]
                continue
            
            # Check similarity with cached embedding (relaxed threshold: 0.30)
            similarity = np.dot(embedding, cache_data['embedding']) / (
                np.linalg.norm(embedding) * np.linalg.norm(cache_data['embedding'])
            )
            
            if similarity >= 0.30:  # Relaxed threshold for 10-second grace period
                # Update cache with new embedding
                self.recent_known_cache[person_id] = {
                    'embedding': embedding.copy(),
                    'timestamp': current_time,
                    'name': cache_data['name']
                }
                logger.debug(f"Grace period match: {person_id} (similarity={similarity:.3f}, "
                           f"time_since_seen={time_since_seen:.1f}s)")
                return person_id, cache_data['name'], float(similarity)
        
        # SECOND: Check against full database with normal threshold
        best_match_id = None
        best_match_name = None
        best_similarity = 0.0
        
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
        
        # Check if similarity exceeds threshold
        if best_similarity >= self.similarity_threshold:
            # Add to recent cache
            self.recent_known_cache[best_match_id] = {
                'embedding': embedding.copy(),
                'timestamp': current_time,
                'name': best_match_name
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
            "model_name": "insightface buffalo_l",
            "detector": "RetinaFace",
            "recognizer": "ArcFace",
            "embedding_dim": 512,
            "similarity_threshold": self.similarity_threshold,
            "known_persons": len(self.known_faces)
        }

