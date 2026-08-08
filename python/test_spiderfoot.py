import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meraglym.osint.general.spiderfoot import SpiderFootAdapter

async def main():
    adapter = SpiderFootAdapter()
    print("Testing SpiderFootAdapter...")
    try:
        payload = {"value": "example.com"}
        results = await adapter.execute(payload)
        print(f"Success! Found {len(results)} observations.")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
