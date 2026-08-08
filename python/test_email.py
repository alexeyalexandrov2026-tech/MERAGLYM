import asyncio
import os
import sys

# Add python dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from meraglym.osint.general.email import EmailAdapter

async def main():
    adapter = EmailAdapter()
    print("Testing EmailAdapter...")
    try:
        payload = {"value": "test@gmail.com"}
        results = await adapter.execute(payload)
        print(f"Success! Found {len(results)} observations.")
    except Exception as e:
        print(f"Failed with expected error (or unexpected): {e}")

if __name__ == "__main__":
    asyncio.run(main())
