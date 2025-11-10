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


@dataclass
class PersonROI:
    """Person ROI tracking for reuse optimization"""
    person_id: str
    bbox: np.ndarray
    roi_image: np.ndarray  # Enlarged face ROI
    embedding: np.ndarray
    last_updated: float
    frame_count: int


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

        # ROI reuse optimization: Track person ROIs for intermediate frames
        # Format: {person_id: PersonROI}
        self.person_rois: Dict[str, PersonROI] = {}
        self.roi_frame_count = 0

        # Matrix optimization: Pre-computed embedding matrix for fast similarity search
        self.database_matrix: Optional[np.ndarray] = None  # (N, 512) matrix of all embeddings
        self.person_ids: List[str] = []  # Corresponding person IDs for matrix rows
        self.person_names: List[str] = []  # Corresponding person names for matrix rows
        
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

            # Build embedding matrix for fast similarity search
            self.rebuild_embedding_matrix()
        except FileNotFoundError:
            logger.error(f"Face database not found at {self.database_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading face database: {e}")
            raise

    def rebuild_embedding_matrix(self):
        """
        Rebuild the embedding matrix from current database
        Called after database loading or updates
        """
        if not self.known_faces:
            self.database_matrix = None
            self.person_ids = []
            self.person_names = []
            logger.info("Embedding matrix cleared (empty database)")
            return

        # Collect all embeddings and metadata
        all_embeddings = []
        person_ids = []
        person_names = []

        for person_id, face_data in self.known_faces.items():
            # Skip persons with no embeddings
            if not face_data.get('embeddings') or len(face_data['embeddings']) == 0:
                logger.warning(f"Skipping {person_id}: no embeddings available")
                continue
            
            # Use the most recent embedding for each person (or centroid if hysteresis enabled)
            if self.use_hysteresis and 'centroid' in face_data:
                embedding = face_data['centroid']
            else:
                # Use the first (most recent) embedding
                embedding = face_data['embeddings'][0]

            # L2 normalize the embedding (ensure unit length for cosine similarity)
            embedding = embedding / np.linalg.norm(embedding)

            all_embeddings.append(embedding)
            person_ids.append(person_id)
            person_names.append(face_data['name'])

        # Create the matrix (handle empty database case)
        if len(all_embeddings) == 0:
            self.database_matrix = None
            self.person_ids = []
            self.person_names = []
            logger.warning("No valid embeddings found in database - all persons will be treated as unknown")
        else:
            self.database_matrix = np.vstack(all_embeddings)  # Shape: (N, 512)
            self.person_ids = person_ids
            self.person_names = person_names
            logger.info(f"Built embedding matrix: {self.database_matrix.shape} for {len(person_ids)} persons")

    def _recognize_with_matrix(self, embedding: np.ndarray) -> Tuple[Optional[str], Optional[str], float]:
        """
        Fast recognition using pre-computed embedding matrix
        Returns best match using matrix dot product (cosine similarity)
        """
        if self.database_matrix is None or self.database_matrix.size == 0:
            return None, None, 0.0

        # L2 normalize the probe embedding
        probe_norm = embedding / np.linalg.norm(embedding)

        # Compute all similarities at once: matrix dot product
        similarities = np.dot(self.database_matrix, probe_norm)  # Shape: (N,)

        # Find best match
        best_idx = np.argmax(similarities)
        best_similarity = similarities[best_idx]

        best_person_id = self.person_ids[best_idx]
        best_person_name = self.person_names[best_idx]

        return best_person_id, best_person_name, float(best_similarity)

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

        # Rebuild matrix after centroid update (for matrix-based recognition)
        if self.database_matrix is not None:
            self.rebuild_embedding_matrix()

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
        # Use matrix-based recognition for massive speedup
        best_match_id, best_match_name, best_similarity = self._recognize_with_matrix(embedding)

        # Get person data for hysteresis logic
        best_person_data = self.known_faces.get(best_match_id) if best_match_id else None

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

    def _compute_roi_iou(self, bbox1: np.ndarray, bbox2: np.ndarray) -> float:
        """Compute IoU between two bounding boxes for ROI comparison"""
        # Convert to [x1, y1, x2, y2] format
        b1 = bbox1.astype(float)
        b2 = bbox2.astype(float)

        # Calculate intersection
        x1 = max(b1[0], b2[0])
        y1 = max(b1[1], b2[1])
        x2 = min(b1[2], b2[2])
        y2 = min(b1[3], b2[3])

        intersection = max(0, x2 - x1) * max(0, y2 - y1)

        # Calculate union
        area1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
        area2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0.0

    def _extract_face_roi(self, frame: np.ndarray, bbox: np.ndarray, expand_factor: float = 1.5) -> np.ndarray:
        """Extract and enlarge face ROI from frame"""
        x1, y1, x2, y2 = bbox.astype(int)

        # Calculate center and size
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        width = int((x2 - x1) * expand_factor)
        height = int((y2 - y1) * expand_factor)

        # Calculate expanded bbox
        roi_x1 = max(0, center_x - width // 2)
        roi_y1 = max(0, center_y - height // 2)
        roi_x2 = min(frame.shape[1], center_x + width // 2)
        roi_y2 = min(frame.shape[0], center_y + height // 2)

        # Extract ROI
        roi = frame[roi_y1:roi_y2, roi_x1:roi_x2]

        return roi

    def _should_reuse_roi(self, person_roi: PersonROI, current_bbox: np.ndarray, current_roi: np.ndarray) -> bool:
        """Check if ROI can be reused (IoU > 0.5)"""
        iou = self._compute_roi_iou(person_roi.bbox, current_bbox)

        # Reuse if IoU is high enough (ROI hasn't moved much)
        return iou >= 0.5

    def process_frame_with_roi_reuse(self, frame: np.ndarray, is_detection_frame: bool = True) -> List[RecognitionResult]:
        """
        Process frame with ROI reuse optimization

        Args:
            frame: Input image (BGR format)
            is_detection_frame: True for full detection, False for ROI reuse mode

        Returns:
            List of RecognitionResult objects
        """
        results = []

        if is_detection_frame:
            # Full detection frame: detect all faces and update ROIs
            detections = self.detect_faces(frame)

            for detection in detections:
                person_id, person_name, similarity = self.recognize_face(detection.embedding)

                # Extract and store ROI for this person
                roi_image = self._extract_face_roi(frame, detection.bbox)

                if person_id:
                    # Update ROI cache for known persons
                    person_roi = PersonROI(
                        person_id=person_id,
                        bbox=detection.bbox.copy(),
                        roi_image=roi_image,
                        embedding=detection.embedding.copy(),
                        last_updated=time.time(),
                        frame_count=self.roi_frame_count
                    )
                    self.person_rois[person_id] = person_roi

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

            # Clean up old ROIs (older than 30 seconds)
            current_time = time.time()
            expired_rois = [pid for pid, roi in self.person_rois.items()
                           if current_time - roi.last_updated > 30.0]
            for pid in expired_rois:
                del self.person_rois[pid]

        else:
            # ROI reuse frame: check existing ROIs without full detection
            for person_id, person_roi in list(self.person_rois.items()):
                # Check if ROI is still valid (placeholder - could add blur/pose checks)
                # For now, just reuse the embedding
                result = RecognitionResult(
                    bbox=person_roi.bbox,
                    embedding=person_roi.embedding,
                    confidence=1.0,  # Assume high confidence for cached
                    person_id=person_id,
                    person_name=self.known_faces.get(person_id, {}).get('name', 'Unknown'),
                    similarity=1.0,  # Assume perfect match for cached
                    is_known=True
                )
                results.append(result)

        self.roi_frame_count += 1
        return results

    def get_model_info(self) -> Dict:
        """Get model information for display"""
        # Get embedding dimension dynamically from database matrix or model
        embedding_dim = None
        if self.database_matrix is not None:
            embedding_dim = self.database_matrix.shape[1]
        elif self.known_faces:
            # Try to get from first available embedding
            for face_data in self.known_faces.values():
                if face_data.get('embeddings') and len(face_data['embeddings']) > 0:
                    embedding_dim = face_data['embeddings'][0].shape[0]
                    break
        else:
            # Default for InsightFace models (buffalo_s and buffalo_l both use 512)
            embedding_dim = 512
        
        # Get detector and recognizer info from InsightFace model
        # InsightFace models use RetinaFace for detection and ArcFace for recognition
        detector = "RetinaFace"  # Standard for InsightFace models
        recognizer = "ArcFace"   # Standard for InsightFace models
        
        return {
            "model_name": f"insightface {self.model_name}",
            "detector": detector,
            "recognizer": recognizer,
            "embedding_dim": embedding_dim,
            "similarity_threshold": self.similarity_threshold,
            "known_persons": len(self.known_faces)
        }

