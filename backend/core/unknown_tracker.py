"""
Unknown Person Tracker with cooldown management
Prevents duplicate alerts for the same unknown person
"""
import time
import numpy as np
import cv2
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class UnknownPerson:
    """Tracked unknown person"""
    uid: str  # Unique identifier
    first_seen: float  # Timestamp of first detection
    last_seen: float  # Timestamp of last detection
    embedding: np.ndarray  # Representative embedding (averaged)
    embedding_history: List[np.ndarray] = field(default_factory=list)  # Last N embeddings for averaging
    snapshot_path: Optional[str] = None
    detection_count: int = 1
    alerted: bool = False  # Whether alert has been sent


class UnknownPersonTracker:
    """
    Tracks unknown persons with cooldown to prevent duplicate alerts
    Uses embedding similarity to identify same person
    """
    
    def __init__(self, cooldown_seconds: float = 300, 
                 similarity_threshold: float = 0.65,
                 snapshot_dir: str = "snapshots",
                 min_detections_before_alert: int = 3,
                 max_embedding_history: int = 5):
        """
        Initialize unknown person tracker
        
        Args:
            cooldown_seconds: Cooldown period before re-alerting same person
            similarity_threshold: Embedding similarity to consider same person
            snapshot_dir: Directory to save snapshots
            min_detections_before_alert: Minimum detections before triggering alert
            max_embedding_history: Maximum embeddings to keep for averaging
        """
        self.cooldown_seconds = cooldown_seconds
        self.similarity_threshold = similarity_threshold
        self.snapshot_dir = snapshot_dir
        self.min_detections_before_alert = min_detections_before_alert
        self.max_embedding_history = max_embedding_history
        
        self.unknown_persons: Dict[str, UnknownPerson] = {}
        self.next_uid = 1
        
        os.makedirs(snapshot_dir, exist_ok=True)
        logger.info(f"UnknownPersonTracker initialized (cooldown={cooldown_seconds}s, "
                   f"similarity={similarity_threshold}, min_detections={min_detections_before_alert})")
    
    def _generate_uid(self) -> str:
        """Generate unique identifier for unknown person"""
        uid = f"UNKNOWN_{self.next_uid:04d}"
        self.next_uid += 1
        return uid
    
    def _compute_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings"""
        return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
    
    def _update_embedding_average(self, person: UnknownPerson, new_embedding: np.ndarray):
        """
        Update person's embedding with moving average
        
        Args:
            person: UnknownPerson object to update
            new_embedding: New embedding to add to history
        """
        # Add new embedding to history
        person.embedding_history.append(new_embedding.copy())
        
        # Keep only last N embeddings
        if len(person.embedding_history) > self.max_embedding_history:
            person.embedding_history.pop(0)
        
        # Update representative embedding as average of history
        person.embedding = np.mean(person.embedding_history, axis=0)
        
        # Re-normalize
        person.embedding = person.embedding / np.linalg.norm(person.embedding)
    
    def _find_matching_unknown(self, embedding: np.ndarray) -> Optional[str]:
        """
        Find if embedding matches any tracked unknown person
        
        Args:
            embedding: Face embedding to match
            
        Returns:
            UID of matching unknown person, or None
        """
        best_match_uid = None
        best_similarity = 0.0
        
        # Search through all tracked persons (including those outside cooldown)
        for uid, person in self.unknown_persons.items():
            similarity = self._compute_similarity(embedding, person.embedding)
            
            if similarity >= self.similarity_threshold and similarity > best_similarity:
                best_similarity = similarity
                best_match_uid = uid
        
        if best_match_uid:
            logger.debug(f"Matched to {best_match_uid} with similarity {best_similarity:.3f}")
        
        return best_match_uid
    
    def _save_snapshot(self, frame: np.ndarray, bbox: np.ndarray, uid: str) -> str:
        """
        Save face snapshot to disk
        
        Args:
            frame: Full frame image
            bbox: Face bounding box [x1, y1, x2, y2]
            uid: Unique identifier
            
        Returns:
            Path to saved snapshot
        """
        try:
            # Extract face region with padding
            x1, y1, x2, y2 = bbox.astype(int)
            h, w = frame.shape[:2]
            
            # Add 20% padding
            pad_x = int((x2 - x1) * 0.2)
            pad_y = int((y2 - y1) * 0.2)
            
            x1 = max(0, x1 - pad_x)
            y1 = max(0, y1 - pad_y)
            x2 = min(w, x2 + pad_x)
            y2 = min(h, y2 + pad_y)
            
            face_img = frame[y1:y2, x1:x2]
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{uid}_{timestamp}.jpg"
            filepath = os.path.join(self.snapshot_dir, filename)
            
            # Save image
            cv2.imwrite(filepath, face_img)
            logger.info(f"Saved snapshot: {filename}")
            
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving snapshot: {e}")
            return None
    
    def check_unknown_person(self, embedding: np.ndarray, frame: np.ndarray, 
                            bbox: np.ndarray) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check if unknown person should trigger alert
        
        Phase 1 Improvements:
        - Uses moving average of embeddings for better matching
        - Requires multiple detections before alerting (default: 3)
        - Relaxed similarity threshold for better deduplication
        
        Args:
            embedding: Face embedding
            frame: Full frame for snapshot
            bbox: Face bounding box
            
        Returns:
            Tuple of (should_alert, uid, snapshot_path)
        """
        current_time = time.time()
        
        # Try to match against existing unknown persons
        matching_uid = self._find_matching_unknown(embedding)
        
        if matching_uid:
            # Found existing unknown person
            person = self.unknown_persons[matching_uid]
            person.last_seen = current_time
            person.detection_count += 1
            
            # Update embedding with moving average
            self._update_embedding_average(person, embedding)
            
            # Check if cooldown has expired
            time_since_first_alert = current_time - person.first_seen
            in_cooldown = person.alerted and (time_since_first_alert < self.cooldown_seconds)
            
            # Check if should alert
            should_alert = (
                person.detection_count >= self.min_detections_before_alert and
                not person.alerted and
                not in_cooldown
            )
            
            if should_alert:
                # Save snapshot on first alert
                person.snapshot_path = self._save_snapshot(frame, bbox, matching_uid)
                person.alerted = True
                logger.info(f"🚨 Alert: Unknown person {matching_uid} confirmed "
                          f"(detections={person.detection_count})")
                return True, matching_uid, person.snapshot_path
            else:
                if in_cooldown:
                    logger.debug(f"Unknown person {matching_uid} re-detected (cooldown active, "
                               f"detections={person.detection_count})")
                else:
                    logger.debug(f"Unknown person {matching_uid} tracked "
                               f"(detections={person.detection_count}/{self.min_detections_before_alert})")
                return False, matching_uid, person.snapshot_path
        
        # New unknown person - create tracking entry (but don't alert yet)
        uid = self._generate_uid()
        
        unknown_person = UnknownPerson(
            uid=uid,
            first_seen=current_time,
            last_seen=current_time,
            embedding=embedding.copy(),
            embedding_history=[embedding.copy()],
            snapshot_path=None,
            detection_count=1,
            alerted=False
        )
        
        self.unknown_persons[uid] = unknown_person
        logger.info(f"👤 New unknown person tracking started: {uid} "
                   f"(need {self.min_detections_before_alert} detections to alert)")
        
        return False, uid, None
    
    def cleanup_expired(self):
        """Remove unknown persons past cooldown period"""
        current_time = time.time()
        expired_uids = []
        
        for uid, person in self.unknown_persons.items():
            if current_time - person.last_seen > self.cooldown_seconds:
                expired_uids.append(uid)
        
        for uid in expired_uids:
            logger.debug(f"Removing expired unknown person: {uid}")
            del self.unknown_persons[uid]
    
    def get_active_unknowns(self) -> List[Dict]:
        """Get list of currently tracked unknown persons"""
        current_time = time.time()
        active = []
        
        for uid, person in self.unknown_persons.items():
            time_remaining = self.cooldown_seconds - (current_time - person.last_seen)
            if time_remaining > 0:
                active.append({
                    'uid': uid,
                    'first_seen': person.first_seen,
                    'last_seen': person.last_seen,
                    'detection_count': person.detection_count,
                    'snapshot_path': person.snapshot_path,
                    'cooldown_remaining': int(time_remaining)
                })
        
        return active
    
    def get_stats(self) -> Dict:
        """Get tracker statistics"""
        return {
            'total_tracked': len(self.unknown_persons),
            'active_cooldowns': len(self.get_active_unknowns()),
            'total_snapshots': self.next_uid - 1
        }
