import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from meraglym.osint.registry import registry
import meraglym.osint

print(f"Total registered adapters: {len(registry._adapters)}")
for k, v in registry._adapters.items():
    print(f" - {k}: {v.__name__}")
