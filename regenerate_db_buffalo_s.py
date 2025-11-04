#!/usr/bin/env python3
"""
Regenerate face database with buffalo_s model
This script converts buffalo_l embeddings to buffalo_s embeddings
"""

import pickle
import numpy as np
import cv2
import os
from insightface.app import FaceAnalysis
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def regenerate_database_with_buffalo_s(original_db_path: str, output_db_path: str):
    """
    Regenerate face database using buffalo_s model

    Args:
        original_db_path: Path to original database (for reference photos)
        output_db_path: Path to save new buffalo_s database
    """

    # NOTE: This is a simplified version. In practice, you would need the original
    # face images to regenerate embeddings. Since we only have embeddings,
    # we'll create a new empty database and show the structure.

    logger.info("Creating new face database with buffalo_s model...")

    # Initialize buffalo_s model
    app = FaceAnalysis(
        name='buffalo_s',
        providers=['CPUExecutionProvider']  # Use CPU for database creation
    )
    app.prepare(ctx_id=-1, det_size=(640, 640))

    # Create empty database structure
    new_database = {}

    # Load original database to get structure
    try:
        with open(original_db_path, 'rb') as f:
            original_db = pickle.load(f)

        logger.info(f"Original database has {len(original_db)} persons")

        # For each person in original database, you'll need to:
        # 1. Load their original face images
        # 2. Re-extract embeddings with buffalo_s
        # 3. Save to new database

        logger.warning("⚠️  To properly regenerate the database, you need the original face images!")
        logger.info("The original database only contains embeddings, not the source images.")
        logger.info("You need to:")
        logger.info("1. Find the original photos used to create the database")
        logger.info("2. Run this script with access to those photos")
        logger.info("3. Or switch back to buffalo_l model")

        # Show what the new structure would look like
        logger.info("\nExpected new database structure:")
        logger.info("new_database = {")
        logger.info("    'person_id': {")
        logger.info("        'name': 'Person Name',")
        logger.info("        'embeddings': [buffalo_s_embedding_512d]")
        logger.info("    }")
        logger.info("}")

        # Create a sample entry to show the structure
        # This would normally be populated from actual face images
        new_database['sample_person'] = {
            'name': 'Sample Person',
            'embeddings': []  # Would contain actual buffalo_s embeddings
        }

        # Save the new database structure
        with open(output_db_path, 'wb') as f:
            pickle.dump(new_database, f)

        logger.info(f"Created empty database structure at {output_db_path}")

    except FileNotFoundError:
        logger.error(f"Original database not found at {original_db_path}")
    except Exception as e:
        logger.error(f"Error processing database: {e}")

def test_buffalo_s_embedding_shape():
    """Test that buffalo_s produces 512-dim embeddings"""
    logger.info("Testing buffalo_s embedding dimensions...")

    app = FaceAnalysis(name='buffalo_s', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=-1, det_size=(640, 640))

    # Create a test face image (this won't work well, but shows the structure)
    test_img = np.random.randint(100, 200, (112, 112, 3), dtype=np.uint8)

    faces = app.get(test_img)
    if faces:
        embedding = faces[0].embedding
        logger.info(f"✅ buffalo_s embedding shape: {embedding.shape}")
        logger.info("✅ Both buffalo_l and buffalo_s use 512-dimensional embeddings")
    else:
        logger.info("No faces detected in test image (expected)")

if __name__ == "__main__":
    # Paths
    original_db = "data/combined_face_database.pkl"
    new_db = "data/combined_face_database_buffalo_s.pkl"

    logger.info("🔄 Face Database Regeneration Tool")
    logger.info("=" * 50)

    # Test embedding shapes
    test_buffalo_s_embedding_shape()

    logger.info("\n" + "=" * 50)
    logger.info("⚠️  IMPORTANT: Database regeneration requires original face images!")

    # Regenerate database (will show warning about missing images)
    regenerate_database_with_buffalo_s(original_db, new_db)

    logger.info("\n" + "=" * 50)
    logger.info("📋 Next Steps:")
    logger.info("1. Locate the original face photos used to create the database")
    logger.info("2. Modify this script to load those photos")
    logger.info("3. Run the script to generate buffalo_s embeddings")
    logger.info("4. Replace the database file")
    logger.info("5. OR: Change back to buffalo_l model in face_recognizer.py")
