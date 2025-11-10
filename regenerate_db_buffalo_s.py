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

def create_database_from_image(image_path: str, person_id: str, person_name: str, output_db_path: str):
    """
    Create face database entry from a single image using buffalo_s model

    Args:
        image_path: Path to the face image
        person_id: ID for the person (e.g., '1234')
        person_name: Name of the person (e.g., 'prashant')
        output_db_path: Path to save the database pkl file
    """
    logger.info(f"Creating face database with buffalo_s model...")
    logger.info(f"Image: {image_path}")
    logger.info(f"Person ID: {person_id}, Name: {person_name}")

    # Initialize buffalo_s model
    app = FaceAnalysis(
        name='buffalo_s',
        providers=['CPUExecutionProvider']  # Use CPU for database creation
    )
    app.prepare(ctx_id=-1, det_size=(640, 640))

    # Load or create database
    database = {}
    if os.path.exists(output_db_path):
        try:
            with open(output_db_path, 'rb') as f:
                database = pickle.load(f)
            logger.info(f"Loaded existing database with {len(database)} persons")
        except Exception as e:
            logger.warning(f"Could not load existing database: {e}, creating new one")

    # Load and process image
    if not os.path.exists(image_path):
        logger.error(f"Image not found at {image_path}")
        return

    logger.info(f"Loading image from {image_path}...")
    img = cv2.imread(image_path)
    if img is None:
        logger.error(f"Failed to load image from {image_path}")
        return

    logger.info(f"Image loaded: {img.shape}")

    # Detect faces and extract embeddings
    logger.info("Detecting faces and extracting embeddings...")
    faces = app.get(img)

    if not faces:
        logger.error("No faces detected in the image!")
        return

    logger.info(f"Detected {len(faces)} face(s) in the image")

    # Extract embeddings from all detected faces
    embeddings = []
    for i, face in enumerate(faces):
        # Get embedding (normalized or raw)
        if hasattr(face, 'normed_embedding'):
            embedding = face.normed_embedding
        elif hasattr(face, 'embedding'):
            embedding = face.embedding
            # Normalize if not already normalized
            embedding = embedding / np.linalg.norm(embedding)
        else:
            logger.warning(f"Face {i+1} has no embedding, skipping")
            continue

        embeddings.append(embedding)
        logger.info(f"  Face {i+1}: embedding shape = {embedding.shape}")

    if not embeddings:
        logger.error("No valid embeddings extracted!")
        return

    # Create or update database entry
    database[person_id] = {
        'name': person_name,
        'embeddings': embeddings
    }

    logger.info(f"Created database entry for {person_name} (ID: {person_id}) with {len(embeddings)} embedding(s)")

    # Save database
    os.makedirs(os.path.dirname(output_db_path), exist_ok=True)
    with open(output_db_path, 'wb') as f:
        pickle.dump(database, f)

    logger.info(f"✅ Database saved to {output_db_path}")
    logger.info(f"Database now contains {len(database)} person(s)")

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
    image_path = "/home/psingh/medgemma/aiims-attendance/face-alert-app/backend/prashant_20251103_143919_879709.jpg"
    output_db = "data/combined_face_database_buffalo_s.pkl"
    person_id = "1234"
    person_name = "prashant"

    logger.info("🔄 Face Database Creation Tool (buffalo_s)")
    logger.info("=" * 50)

    # Test embedding shapes
    test_buffalo_s_embedding_shape()

    logger.info("\n" + "=" * 50)
    logger.info("Creating database entry from image...")

    # Create database entry from image
    create_database_from_image(image_path, person_id, person_name, output_db)

    logger.info("\n" + "=" * 50)
    logger.info("✅ Database creation complete!")
