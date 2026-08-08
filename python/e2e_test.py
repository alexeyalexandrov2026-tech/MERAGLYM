import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meraglym.osint.registry import registry
import meraglym.osint

async def main():
    print(f"--- MERAGLYM E2E PIPELINE TEST ---")
    print(f"Total Registered Adapters: {len(registry._adapters)}\n")
    
    # Define payloads for different adapters
    payloads = {
        "egrul_registry": {"value": "7707083893"},  # Sberbank INN
        "rfsd_financials": {"inn": "7707083893"},
        "kad_arbitr": {"value": "7707083893"},
        "fssp_check": {"value": "7707083893"},
        "efrsb_bankruptcy": {"value": "7707083893"},
        "fns_tax": {"value": "7707083893"},
        "sudrf_courts": {"value": "7707083893"},
        "mvd_wanted": {"value": "1234567890"},
        "stix_ingest": {"objects": [{"type": "threat-actor", "name": "Test Actor"}]},
        "email_recon": {"value": "test@gmail.com"},
        "holehe_recon": {"value": "test@gmail.com"},
        "social_recon": {"value": "example"},
        "geospatial_mapper": {"value": "11:22:33:44:55:66"},
        "metadata_extractor": {"value": "test.jpg"},
        "crypto_recon": {"value": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"},
        "camera_recon": {"value": "camera"},
        "darkweb_mapper": {"value": "http://example.onion"},
        "spiderfoot_meta": {"value": "example.com"},
        "opencti_connector": {"value": "1.1.1.1"}
    }
    
    results = {}
    
    for identifier, adapter_class in registry._adapters.items():
        print(f"Executing: {identifier}...")
        adapter = adapter_class()
        payload = payloads.get(identifier, {"value": "test"})
        
        try:
            # We timeout each to prevent infinite hanging
            obs = await asyncio.wait_for(adapter.execute(payload), timeout=10.0)
            results[identifier] = f"SUCCESS - {len(obs)} observations"
            print(f"  -> SUCCESS ({len(obs)} observations)")
        except asyncio.TimeoutError:
            results[identifier] = "TIMEOUT"
            print(f"  -> TIMEOUT")
        except Exception as e:
            err = str(e)
            if "EXTERNAL_DEPENDENCY_UNAVAILABLE" in err:
                results[identifier] = "GRACEFUL FALLBACK (Missing Dep)"
                print(f"  -> GRACEFUL: {err}")
            elif "REQUIRES_USER_CREDENTIAL" in err:
                results[identifier] = "REQUIRES_USER_CREDENTIAL (Missing Token/Auth)"
                print(f"  -> GRACEFUL: {err}")
            elif "REQUIRES_EXTERNAL_SERVICE" in err:
                results[identifier] = "REQUIRES_EXTERNAL_SERVICE (API Blocked/Offline)"
                print(f"  -> GRACEFUL: {err}")
            elif "SourceUnavailableError" in err or "RateLimitedError" in err or "RateLimitError" in err:
                results[identifier] = "REQUIRES_EXTERNAL_SERVICE (API RateLimit/Blocked)"
                print(f"  -> GRACEFUL API: {err}")
            else:
                results[identifier] = f"ERROR: {err}"
                print(f"  -> ERROR: {err}")
                
    print("\n--- SUMMARY ---")
    for identifier, status in results.items():
        print(f"{identifier.ljust(20)} : {status}")

if __name__ == "__main__":
    asyncio.run(main())
