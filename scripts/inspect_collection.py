#!/usr/bin/env python3
"""
Inspect Qdrant collection for duplicates
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()

from src.server import qdrant_client, COLLECTION_NAME
import json

def main():
    """Inspect all points in collection"""
    print("\n🔍 Inspecting Collection")
    print("=" * 80)

    # Get collection info
    collection = qdrant_client.get_collection(collection_name=COLLECTION_NAME)
    print(f"Total points: {collection.points_count}\n")

    # Scroll through all points
    scroll_result = qdrant_client.scroll(
        collection_name=COLLECTION_NAME,
        limit=100,
        with_vectors=False,
        with_payload=True
    )

    points = scroll_result[0]

    # Track IDs and text content
    id_count = {}
    text_count = {}

    print("All points:")
    print("-" * 80)
    for point in points:
        point_id = point.id
        text = point.payload.get('text', '')
        branch = point.payload.get('branch_id', 'unknown')
        timestamp = point.payload.get('timestamp', 'N/A')

        # Count occurrences
        id_count[point_id] = id_count.get(point_id, 0) + 1
        text_preview = text[:60]
        text_count[text_preview] = text_count.get(text_preview, 0) + 1

        print(f"ID: {point_id}")
        print(f"  Branch: {branch}")
        print(f"  Text: {text_preview}...")
        print(f"  Timestamp: {timestamp}")
        print()

    # Find duplicates
    print("=" * 80)
    print("\n🔎 Duplicate Analysis:")
    print("-" * 80)

    duplicate_ids = {k: v for k, v in id_count.items() if v > 1}
    duplicate_texts = {k: v for k, v in text_count.items() if v > 1}

    if duplicate_ids:
        print(f"\n⚠️  Found {len(duplicate_ids)} duplicate IDs:")
        for point_id, count in duplicate_ids.items():
            print(f"  ID {point_id}: appears {count} times")
    else:
        print("\n✓ No duplicate IDs found")

    if duplicate_texts:
        print(f"\n⚠️  Found {len(duplicate_texts)} duplicate texts:")
        for text, count in duplicate_texts.items():
            print(f"  '{text}...': appears {count} times")
    else:
        print("\n✓ No duplicate texts found")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
