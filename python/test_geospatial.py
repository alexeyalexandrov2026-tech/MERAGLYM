import asyncio
import os
import sys

# Add python dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from meraglym.osint.general.geospatial import GeospatialAdapter

async def main():
    adapter = GeospatialAdapter()
    print("Testing GeospatialAdapter...")
    try:
        payload = {"value": "11:22:33:44:55:66"}
        results = await adapter.execute(payload)
        print(f"Success! Found {len(results)} observations.")
    except Exception as e:
        print(f"Failed with expected error (or unexpected): {e}")

if __name__ == "__main__":
    asyncio.run(main())
