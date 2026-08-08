import asyncio
import os
import sys

# Add python dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from meraglym.osint.general.social import SocialMediaAdapter

async def main():
    adapter = SocialMediaAdapter()
    print("Testing SocialMediaAdapter...")
    try:
        # Use a safe target for test
        payload = {"value": "example"}
        results = await adapter.execute(payload)
        print(f"Success! Found {len(results)} observations.")
        for r in results[:5]:
            print(r)
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
