#!/usr/bin/env python3
"""Quick test for Sherlock integration"""

import os
import sys

# Set UTF-8 encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.dragnet import Dragnet

print("=" * 70)
print("SHERLOCK INTEGRATION TEST")
print("=" * 70)
print()

# Test with a simple username
target = "testuser"
print(f"Testing Sherlock with target: {target}")
print()

dragnet = Dragnet(target)
print("[1/2] Running Sherlock...")
success = dragnet.run_sherlock()

if success:
    print(f"✅ Sherlock completed successfully!")
    print(f"   Found {len(dragnet.leads)} potential accounts")
    if dragnet.leads:
        print(f"\n   Sample results:")
        for lead in dragnet.leads[:5]:
            print(f"   - {lead}")
else:
    print("❌ Sherlock encountered issues")

print()
print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)
