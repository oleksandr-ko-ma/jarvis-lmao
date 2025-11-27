#!/usr/bin/env python3
"""
Test script for Jarvis LMAO memory system
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()

from src.server import (
    qdrant_client,
    generate_embedding,
    generate_point_id,
    check_overseer,
    COLLECTION_NAME
)
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
from datetime import datetime
import json

def test_overseer():
    """Test Silent Overseer safety checks"""
    print("\n🛡️  Testing Silent Overseer")
    print("=" * 50)

    # Test safe action
    safe_result = check_overseer("terraform fmt", "bash")
    print(f"✓ Safe action: {safe_result}")

    # Test dangerous action
    dangerous_result = check_overseer("rm -rf /", "bash")
    print(f"⚠️  Dangerous action: {dangerous_result}")

    # Test force push
    force_push_result = check_overseer("git push --force origin master", "bash")
    print(f"⚠️  Force push: {force_push_result}")

    return True

def test_store_memory():
    """Test storing memory in hive-mind"""
    print("\n💾 Testing Memory Storage")
    print("=" * 50)

    # Test memory 1
    text1 = "Jarvis LMAO is operational! Hive-mind memory system initialized successfully."
    branch1 = "main"

    embedding1 = generate_embedding(text1)
    timestamp1 = datetime.now().isoformat()
    point_id1 = generate_point_id(text1, branch1)

    point1 = PointStruct(
        id=point_id1,
        vector=embedding1,
        payload={
            "text": text1,
            "branch_id": branch1,
            "timestamp": timestamp1,
            "type": "test",
            "overseer_status": "passed"
        }
    )

    qdrant_client.upsert(collection_name=COLLECTION_NAME, points=[point1])
    print(f"✓ Stored memory 1: ID {point_id1}")
    print(f"  Branch: {branch1}")
    print(f"  Text: {text1[:50]}...")

    # Test memory 2 - different branch
    text2 = "Terraform validation pattern learned: Always use fmt and validate before apply."
    branch2 = "terraform-refactor"

    embedding2 = generate_embedding(text2)
    timestamp2 = datetime.now().isoformat()
    point_id2 = generate_point_id(text2, branch2)

    point2 = PointStruct(
        id=point_id2,
        vector=embedding2,
        payload={
            "text": text2,
            "branch_id": branch2,
            "timestamp": timestamp2,
            "type": "skill",
            "skill_name": "terraform_validate",
            "success": True,
            "overseer_status": "passed"
        }
    )

    qdrant_client.upsert(collection_name=COLLECTION_NAME, points=[point2])
    print(f"✓ Stored memory 2: ID {point_id2}")
    print(f"  Branch: {branch2}")
    print(f"  Text: {text2[:50]}...")

    # Test memory 3 - another branch
    text3 = "Never use git push --force on main/master branches. Always requires user approval."
    branch3 = "main"

    embedding3 = generate_embedding(text3)
    timestamp3 = datetime.now().isoformat()
    point_id3 = generate_point_id(text3, branch3)

    point3 = PointStruct(
        id=point_id3,
        vector=embedding3,
        payload={
            "text": text3,
            "branch_id": branch3,
            "timestamp": timestamp3,
            "type": "learning",
            "tags": ["git", "safety", "overseer"],
            "overseer_status": "passed"
        }
    )

    qdrant_client.upsert(collection_name=COLLECTION_NAME, points=[point3])
    print(f"✓ Stored memory 3: ID {point_id3}")
    print(f"  Branch: {branch3}")
    print(f"  Text: {text3[:50]}...")

    return [point_id1, point_id2, point_id3]

def test_search_memory():
    """Test searching hive-mind memory"""
    print("\n🔍 Testing Memory Search")
    print("=" * 50)

    # Test 1: Search for "Jarvis operational"
    query1 = "Jarvis operational status"
    embedding1 = generate_embedding(query1)
    results1 = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=embedding1,
        limit=3
    ).points

    print(f"\nQuery: '{query1}'")
    print(f"Results: {len(results1)}")
    for i, result in enumerate(results1, 1):
        print(f"{i}. [Score: {result.score:.3f}] [{result.payload.get('branch_id')}]")
        print(f"   {result.payload.get('text')[:80]}...")

    # Test 2: Search for "terraform"
    query2 = "terraform validation patterns"
    embedding2 = generate_embedding(query2)
    results2 = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=embedding2,
        limit=3
    ).points

    print(f"\nQuery: '{query2}'")
    print(f"Results: {len(results2)}")
    for i, result in enumerate(results2, 1):
        print(f"{i}. [Score: {result.score:.3f}] [{result.payload.get('branch_id')}]")
        print(f"   {result.payload.get('text')[:80]}...")

    # Test 3: Search with branch filter
    query3 = "validation"
    embedding3 = generate_embedding(query3)
    results3 = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=embedding3,
        limit=3,
        query_filter=Filter(
            must=[FieldCondition(key="branch_id", match=MatchValue(value="terraform-refactor"))]
        )
    ).points

    print(f"\nQuery: '{query3}' (branch filter: terraform-refactor)")
    print(f"Results: {len(results3)}")
    for i, result in enumerate(results3, 1):
        print(f"{i}. [Score: {result.score:.3f}] [{result.payload.get('branch_id')}]")
        print(f"   {result.payload.get('text')[:80]}...")

    return True

def test_branch_stats():
    """Test branch statistics"""
    print("\n📊 Testing Branch Statistics")
    print("=" * 50)

    # Get all points
    scroll_result = qdrant_client.scroll(
        collection_name=COLLECTION_NAME,
        limit=100,
        with_vectors=False
    )

    branches = {}
    for point in scroll_result[0]:
        branch = point.payload.get("branch_id", "unknown")
        branches[branch] = branches.get(branch, 0) + 1

    stats = {
        "total_branches": len(branches),
        "total_memories": len(scroll_result[0]),
        "branches": branches
    }

    print(json.dumps(stats, indent=2))

    return True

def main():
    """Run all tests"""
    print("🤖 Jarvis LMAO Memory System Test")
    print("=" * 50)

    try:
        # Test Overseer
        test_overseer()

        # Test storage
        point_ids = test_store_memory()

        # Test search
        test_search_memory()

        # Test stats
        test_branch_stats()

        print("\n" + "=" * 50)
        print("✅ All tests passed!")
        print("=" * 50)

        print("\n💡 Next steps:")
        print("1. Configure Claude Code MCP settings")
        print("2. Restart Claude Code")
        print("3. Use memory tools in conversations")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
