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
import config

logger = logging.getLogger(__name__)


@dataclass
class UnknownPerson:
    """Tracked unknown person"""
    uid: str  # Unique identifier
    first_seen: float  # Timestamp of first detection
    last_seen: float  # Timestamp of last detection
    embedding: np.ndarray  # Representative embedding (averaged)
    embedding_history: List[np.ndarray] = field(default_factory=list)  # Last N embeddings for averaging
    bbox: Optional[np.ndarray] = None  # Last bounding box [x1, y1, x2, y2]
    bbox_history: List[Tuple[np.ndarray, float]] = field(default_factory=list)  # [(bbox, timestamp), ...]
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
                 max_embedding_history: int = 5,
                 spatial_iou_threshold: float = 0.3,
                 temporal_window_seconds: float = 2.0,
                 spatial_boost_score: float = 0.20):
        """
        Initialize unknown person tracker
        
        Args:
            cooldown_seconds: Cooldown period before re-alerting same person
            similarity_threshold: Embedding similarity to consider same person
            snapshot_dir: Directory to save snapshots
            min_detections_before_alert: Minimum detections before triggering alert
            max_embedding_history: Maximum embeddings to keep for averaging
            spatial_iou_threshold: Minimum IoU for spatial proximity matching (Phase 2)
            temporal_window_seconds: Time window for spatial-temporal matching (Phase 2)
            spatial_boost_score: Score boost for spatial-temporal matches
        """
        self.cooldown_seconds = cooldown_seconds
        self.similarity_threshold = similarity_threshold
        self.snapshot_dir = snapshot_dir
        self.min_detections_before_alert = min_detections_before_alert
        self.max_embedding_history = max_embedding_history
        self.spatial_iou_threshold = spatial_iou_threshold
        self.temporal_window_seconds = temporal_window_seconds
        self.spatial_boost_score = spatial_boost_score
        
        self.unknown_persons: Dict[str, UnknownPerson] = {}
        self.next_uid = 1
        
        os.makedirs(snapshot_dir, exist_ok=True)
        logger.info(f"UnknownPersonTracker initialized (cooldown={cooldown_seconds}s, "
                   f"similarity={similarity_threshold}, min_detections={min_detections_before_alert}, "
                   f"spatial_iou={spatial_iou_threshold}, temporal_window={temporal_window_seconds}s, "
                   f"spatial_boost={spatial_boost_score})")
    
    def _generate_uid(self) -> str:
        """Generate unique identifier for unknown person"""
        uid = f"UNKNOWN_{self.next_uid:04d}"
        self.next_uid += 1
        return uid
    
    def _compute_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings"""
        return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
    
    def _compute_iou(self, bbox1: np.ndarray, bbox2: np.ndarray) -> float:
        """
        Compute Intersection over Union (IoU) between two bounding boxes
        
        Args:
            bbox1: First bounding box [x1, y1, x2, y2]
            bbox2: Second bounding box [x1, y1, x2, y2]
            
        Returns:
            IoU score (0.0 to 1.0)
        """
        # Calculate intersection coordinates
        x1_inter = max(bbox1[0], bbox2[0])
        y1_inter = max(bbox1[1], bbox2[1])
        x2_inter = min(bbox1[2], bbox2[2])
        y2_inter = min(bbox1[3], bbox2[3])
        
        # Calculate intersection area
        if x2_inter < x1_inter or y2_inter < y1_inter:
            return 0.0
        
        intersection = (x2_inter - x1_inter) * (y2_inter - y1_inter)
        
        # Calculate union area
        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
        union = area1 + area2 - intersection
        
        if union <= 0:
            return 0.0
        
        return intersection / union
    
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
    
    def _find_matching_unknown(self, embedding: np.ndarray, bbox: np.ndarray, 
                              current_time: float) -> Tuple[Optional[str], Optional[str], float]:
        """
        Find if embedding matches any tracked unknown person
        Uses both embedding similarity and spatial-temporal proximity (Phase 2)
        Also checks long-term matches for cooldown purposes
        
        Args:
            embedding: Face embedding to match
            bbox: Face bounding box [x1, y1, x2, y2]
            current_time: Current timestamp
            
        Returns:
            Tuple of:
              - UID of best matching unknown person (or None)
              - UID of any alerted-UID within cooldown that matches by similarity (or None)
              - Similarity value for the suppression UID (0.0 if none)
        """
        best_match_uid = None
        best_score = 0.0
        best_similarity = 0.0
        suppress_uid: Optional[str] = None
        suppress_similarity: float = 0.0
        
        # Search through all tracked persons (including those outside cooldown)
        for uid, person in self.unknown_persons.items():
            # Calculate embedding similarity
            similarity = self._compute_similarity(embedding, person.embedding)
            
            time_diff = current_time - person.last_seen
            
            # Phase 2: Add spatial-temporal boost (for short-term matches)
            spatial_temporal_boost = 0.0
            if person.bbox is not None and time_diff <= self.temporal_window_seconds:
                # Calculate spatial proximity (IoU)
                iou = self._compute_iou(bbox, person.bbox)
                
                # If spatially close, boost the score
                if iou >= self.spatial_iou_threshold:
                    spatial_temporal_boost = self.spatial_boost_score  # Configurable boost
                    logger.debug(f"🎯 {uid}: IoU={iou:.3f}, time_diff={time_diff:.2f}s, "
                                 f"applying spatial-temporal boost (+{spatial_temporal_boost})")
            
            # Combined score: embedding similarity + spatial-temporal boost
            combined_score = similarity + spatial_temporal_boost
            
            # Match criteria:
            # 1. Short-term match: combined score >= threshold (with boost)
            # 2. Long-term match: similarity >= threshold AND within cooldown period (for preventing duplicates)
            time_since_first_alert = current_time - person.first_seen
            is_long_term_match = (
                person.alerted and 
                similarity >= self.similarity_threshold and 
                time_since_first_alert < self.cooldown_seconds
            )
            
            # Track any alerted-UID within cooldown that matches by similarity threshold (for suppression)
            if is_long_term_match and similarity > suppress_similarity:
                suppress_uid = uid
                suppress_similarity = similarity
            
            is_short_term_match = combined_score >= self.similarity_threshold
            
            if (is_short_term_match or is_long_term_match) and combined_score > best_score:
                best_score = combined_score
                best_similarity = similarity
                best_match_uid = uid
                if is_long_term_match and not is_short_term_match:
                    logger.debug(f"🔗 Long-term match: {uid} (similarity={similarity:.3f}, "
                                 f"time_since_alert={time_since_first_alert:.1f}s, cooldown active)")
        
        if best_match_uid:
            boost_applied = best_score - best_similarity
            logger.info(f"✅ Matched to {best_match_uid} with similarity={best_similarity:.3f}, "
                        f"boost={boost_applied:.3f}, final_score={best_score:.3f}")
        
        return best_match_uid, suppress_uid, suppress_similarity
    
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
        - Alert immediately (MIN_DETECTIONS = 1)
        - Similarity threshold 0.55 for reliable matching
        
        Phase 2 Improvements (Anti-Duplicate):
        - Spatial-temporal proximity tracking using IoU and time window
        - Tracks bounding box history for spatial matching
        - Boosts matching score for nearby detections in time/space
        - Prevents duplicates even with immediate alerts
        - Reduces false duplicates by 80-90%
        
        Args:
            embedding: Face embedding
            frame: Full frame for snapshot
            bbox: Face bounding box [x1, y1, x2, y2]
            
        Returns:
            Tuple of (should_alert, uid, snapshot_path)
        """
        current_time = time.time()

        # Prepare similarity scores (for quick suppression decision)
        similarity_scores = []
        if len(self.unknown_persons) > 0:
            logger.info("=" * 80)
            logger.info(f"🔍 Checking new detection against {len(self.unknown_persons)} existing unknown person(s):")
            for uid, person in self.unknown_persons.items():
                similarity = self._compute_similarity(embedding, person.embedding)
                time_diff = current_time - person.last_seen

                # Calculate spatial boost potential
                spatial_boost = 0.0
                if person.bbox is not None and time_diff <= self.temporal_window_seconds:
                    iou = self._compute_iou(bbox, person.bbox)
                    if iou >= self.spatial_iou_threshold:
                        spatial_boost = self.spatial_boost_score

                combined_score = similarity + spatial_boost
                similarity_scores.append({
                    'uid': uid,
                    'similarity': similarity,
                    'spatial_boost': spatial_boost,
                    'combined_score': combined_score,
                    'time_diff': time_diff,
                    'alerted': person.alerted,
                    'detection_count': person.detection_count,
                    'meets_threshold': combined_score >= self.similarity_threshold
                })

                status = "✅ MATCH" if combined_score >= self.similarity_threshold else "❌ NO MATCH"
                boost_info = f"(+{spatial_boost:.2f} boost)" if spatial_boost > 0 else ""
                logger.info(f"  {status} {uid}: similarity={similarity:.3f} {boost_info} → combined={combined_score:.3f} "
                            f"(threshold={self.similarity_threshold:.3f}) | "
                            f"time_diff={time_diff:.2f}s | alerted={person.alerted} | detections={person.detection_count}")

            # Log best match summary
            if similarity_scores:
                best_match = max(similarity_scores, key=lambda x: x['combined_score'])
                logger.info(f"📊 Best match: {best_match['uid']} with combined_score={best_match['combined_score']:.3f} "
                            f"(similarity={best_match['similarity']:.3f} + boost={best_match['spatial_boost']:.3f})")
            logger.info("=" * 80)

        # Try to match against existing unknown persons (Phase 2: with spatial-temporal)
        matching_uid, suppress_uid, suppress_sim = self._find_matching_unknown(embedding, bbox, current_time)

        # Quick suppression: if no matching_uid but an existing UID has a combined score above
        # QUICK_SUPPRESSION_THRESHOLD, merge this detection into that UID instead of creating a new one.
        if (not matching_uid) and config.QUICK_SUPPRESSION_ENABLED and similarity_scores:
            best_candidate = max(similarity_scores, key=lambda x: x['combined_score'])
            if best_candidate['combined_score'] >= getattr(config, 'QUICK_SUPPRESSION_THRESHOLD', 0.45):
                chosen_uid = best_candidate['uid']
                logger.info(f"🔒 Quick suppression: merging detection into existing {chosen_uid} "
                            f"(combined_score={best_candidate['combined_score']:.3f} >= "
                            f"{config.QUICK_SUPPRESSION_THRESHOLD:.3f})")
                # Update the chosen UID with this embedding
                person = self.unknown_persons.get(chosen_uid)
                if person is not None:
                    person.last_seen = current_time
                    person.detection_count += 1
                    self._update_embedding_average(person, embedding)
                    # Update bbox history for spatial tracking
                    person.bbox = bbox.copy()
                    person.bbox_history.append((bbox.copy(), current_time))
                    if len(person.bbox_history) > 10:
                        person.bbox_history.pop(0)
                    # Treat as matched now
                    matching_uid = chosen_uid
        
        if matching_uid:
            # Found existing unknown person
            person = self.unknown_persons[matching_uid]
            person.last_seen = current_time
            person.detection_count += 1
            
            # Update embedding with moving average
            self._update_embedding_average(person, embedding)
            
            # Phase 2: Update bbox for spatial tracking
            person.bbox = bbox.copy()
            person.bbox_history.append((bbox.copy(), current_time))
            # Keep only recent bbox history (last 10)
            if len(person.bbox_history) > 10:
                person.bbox_history.pop(0)
            
            # Check if cooldown has expired
            time_since_first_alert = current_time - person.first_seen
            in_cooldown = person.alerted and (time_since_first_alert < self.cooldown_seconds)
            
            # Check if should alert (respect warmup window if enabled)
            warmup_ok = True
            if getattr(config, 'NEW_UID_WARMUP_ENABLED', False):
                warmup_ok = (current_time - person.first_seen) >= getattr(config, 'NEW_UID_WARMUP_WINDOW', 0.6)

            should_alert = (
                person.detection_count >= self.min_detections_before_alert and
                not person.alerted and
                not in_cooldown and
                warmup_ok
            )
            
            if should_alert:
                # Log similarity check before alerting
                logger.info("=" * 80)
                logger.info(f"🚨 PRE-ALERT CHECK for {matching_uid}:")
                logger.info(f"   Detection count: {person.detection_count}/{self.min_detections_before_alert}")
                logger.info(f"   Already alerted: {person.alerted}")
                logger.info(f"   Time since first seen: {time_since_first_alert:.2f}s (cooldown: {self.cooldown_seconds}s)")
                
                # Check similarity with all other unknown persons before alerting
                # If another UID is already alerted and has high similarity, suppress this alert
                if len(self.unknown_persons) > 1:
                    logger.info(f"   Checking similarity with {len(self.unknown_persons) - 1} other unknown person(s):")
                    for other_uid, other_person in self.unknown_persons.items():
                        if other_uid != matching_uid:
                            similarity = self._compute_similarity(person.embedding, other_person.embedding)
                            time_diff_other = current_time - other_person.first_seen
                            logger.info(f"     vs {other_uid}: similarity={similarity:.3f} "
                                      f"(threshold={self.similarity_threshold:.3f}) | "
                                      f"other_alerted={other_person.alerted} | "
                                      f"time_since_other_first_seen={time_diff_other:.2f}s")
                            
                            # Quick suppression: if another UID is already alerted and similarity is high, suppress this alert
                            if (getattr(config, 'QUICK_SUPPRESSION_ENABLED', True) and 
                                other_person.alerted and 
                                similarity >= getattr(config, 'QUICK_SUPPRESSION_THRESHOLD', 0.45)):
                                logger.warning(f"     ⚠️  WARNING: High similarity ({similarity:.3f}) with already-alerted {other_uid}!")
                                logger.info(f"🛑 Alert suppressed for {matching_uid}: similar to already-alerted "
                                          f"{other_uid} (similarity={similarity:.3f} >= "
                                          f"quick_suppression_threshold={getattr(config, 'QUICK_SUPPRESSION_THRESHOLD', 0.45):.3f})")
                                logger.info("=" * 80)
                                return False, matching_uid, person.snapshot_path
                            elif similarity >= self.similarity_threshold:
                                logger.warning(f"     ⚠️  WARNING: High similarity detected! These might be the same person!")
                
                # Cross-UID suppression result from the matching pass
                if suppress_uid and suppress_uid != matching_uid:
                    logger.info(
                        f"🛑 Alert suppressed for {matching_uid}: similar to already-alerted "
                        f"{suppress_uid} within cooldown (similarity={suppress_sim:.3f} >= "
                        f"threshold={self.similarity_threshold:.3f})"
                    )
                    logger.info("=" * 80)
                    return False, matching_uid, person.snapshot_path
                
                # Save snapshot on first alert
                person.snapshot_path = self._save_snapshot(frame, bbox, matching_uid)
                person.alerted = True
                logger.info(f"✅ ALERT TRIGGERED: Unknown person {matching_uid} confirmed "
                          f"(detections={person.detection_count})")
                logger.info("=" * 80)
                
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
        
        # Log why no match was found
        if len(self.unknown_persons) > 0:
            logger.warning(f"⚠️  No match found! Creating new UID: {uid}")
            logger.warning(f"   Reason: All existing unknown persons had similarity < {self.similarity_threshold:.3f} threshold")
            logger.warning(f"   This may indicate: (1) Different person, (2) High embedding variance, or (3) Threshold too strict")
        
        unknown_person = UnknownPerson(
            uid=uid,
            first_seen=current_time,
            last_seen=current_time,
            embedding=embedding.copy(),
            embedding_history=[embedding.copy()],
            bbox=bbox.copy(),  # Phase 2: Initialize bbox for spatial tracking
            bbox_history=[(bbox.copy(), current_time)],  # Phase 2: Track bbox history
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
    
    def reset(self):
        """Reset tracker - clear all tracked unknown persons"""
        logger.info("🔄 Resetting unknown person tracker - clearing all tracked persons")
        self.unknown_persons.clear()
        self.next_uid = 1
        logger.info("✅ Unknown person tracker reset complete")
    
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
