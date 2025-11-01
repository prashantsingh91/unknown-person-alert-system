"""
Known Person Tracker to prevent spam
Only shows each known person once per cooldown period
"""
import time
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class KnownPersonTracker:
    """
    Tracks known persons with cooldown to prevent spam
    """
    
    def __init__(self, cooldown_seconds: float = 30):
        """
        Initialize known person tracker
        
        Args:
            cooldown_seconds: Cooldown period before showing same person again
        """
        self.cooldown_seconds = cooldown_seconds
        self.last_seen: Dict[str, float] = {}  # person_id -> timestamp
        logger.info(f"KnownPersonTracker initialized (cooldown={cooldown_seconds}s)")
    
    def should_display(self, person_id: str) -> bool:
        """
        Check if known person should be displayed
        
        Args:
            person_id: ID of known person
            
        Returns:
            True if should display, False if in cooldown
        """
        current_time = time.time()
        
        if person_id not in self.last_seen:
            # First time seeing this person
            self.last_seen[person_id] = current_time
            logger.info(f"✓ Known person detected: {person_id}")
            return True
        
        # Check if cooldown has expired
        time_since_last = current_time - self.last_seen[person_id]
        if time_since_last >= self.cooldown_seconds:
            # Cooldown expired, can show again
            self.last_seen[person_id] = current_time
            logger.info(f"✓ Known person detected again: {person_id} "
                       f"(last seen {time_since_last:.1f}s ago)")
            return True
        
        # Still in cooldown
        logger.debug(f"Known person {person_id} in cooldown "
                    f"({self.cooldown_seconds - time_since_last:.1f}s remaining)")
        return False
    
    def cleanup_expired(self):
        """Remove entries past cooldown period to save memory"""
        current_time = time.time()
        expired_ids = []
        
        for person_id, last_seen in self.last_seen.items():
            if current_time - last_seen > self.cooldown_seconds * 2:  # 2x cooldown
                expired_ids.append(person_id)
        
        for person_id in expired_ids:
            del self.last_seen[person_id]
            logger.debug(f"Removed expired known person: {person_id}")
    
    def get_stats(self) -> Dict:
        """Get tracker statistics"""
        return {
            'total_tracked': len(self.last_seen),
            'cooldown_seconds': self.cooldown_seconds
        }

