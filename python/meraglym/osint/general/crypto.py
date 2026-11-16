import os
import re
from typing import Any, Dict, List

from meraglym.osint import BaseAdapter, registry
from meraglym.osint._util import credential_error, service_error

BTC_RE = re.compile(r"^(bc1[a-z0-9]{25,87}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})$")
ETH_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")


class CryptoAdapter(BaseAdapter):
    """Wallet lookup.

    * Bitcoin: keyless, via the public Esplora API (blockstream.info; override with BTC_ESPLORA_URL).
    * Ethereum: Etherscan API v2, needs ETHERSCAN_API_KEY (BLOCKCHAIN_API_KEY accepted as an alias).
    """
    identifier = "crypto_recon"
    region = "GLOBAL"
    version = "2.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        addr = str(payload.get("value") or "").strip()
        import httpx
        if BTC_RE.match(addr):
            base = os.environ.get("BTC_ESPLORA_URL", "https://blockstream.info/api").rstrip("/")
            try:
                async with httpx.AsyncClient(timeout=30.0) as c:
                    r = await c.get(f"{base}/address/{addr}")
                    r.raise_for_status()
                    info = r.json()
                    t = await c.get(f"{base}/address/{addr}/txs")
                    txs = t.json() if t.status_code == 200 else []
            except Exception as e:
                raise service_error(f"Esplora API error: {e}")
            cs, ms = info.get("chain_stats", {}), info.get("mempool_stats", {})
            balance = cs.get("funded_txo_sum", 0) - cs.get("spent_txo_sum", 0)
            obs = [{
                "entity_type": "CryptoWallet",
                "entity_value": addr,
                "metadata": {
                    "source": "esplora", "chain": "bitcoin", "tx_count": cs.get("tx_count"),
                    "received_btc": cs.get("funded_txo_sum", 0) / 1e8, "sent_btc": cs.get("spent_txo_sum", 0) / 1e8,
                    "balance_btc": balance / 1e8, "mempool_tx_count": ms.get("tx_count"),
                    "recent_txids": [x.get("txid") for x in txs[:10]],
                },
                "confidence": 1.0,
                "reliability": 0.95,
            }]
            return obs
        if ETH_RE.match(addr):
            key = os.environ.get("ETHERSCAN_API_KEY") or os.environ.get("BLOCKCHAIN_API_KEY")
            if not key:
                raise credential_error("Ethereum lookups need ETHERSCAN_API_KEY (free key at etherscan.io/myapikey).")
            try:
                async with httpx.AsyncClient(timeout=30.0) as c:
                    common = {"chainid": 1, "address": addr, "apikey": key}
                    bal = (await c.get("https://api.etherscan.io/v2/api",
                                       params={**common, "module": "account", "action": "balance", "tag": "latest"})).json()
                    txs = (await c.get("https://api.etherscan.io/v2/api",
                                       params={**common, "module": "account", "action": "txlist", "page": 1,
                                               "offset": 10, "sort": "desc"})).json()
            except Exception as e:
                raise service_error(f"Etherscan API error: {e}")
            if str(bal.get("status")) != "1":
                msg = str(bal.get("result") or bal.get("message"))
                if "key" in msg.lower():
                    raise credential_error(f"Etherscan rejected the API key: {msg}")
                raise service_error(f"Etherscan: {msg}")
            tx_list = txs.get("result") if isinstance(txs.get("result"), list) else []
            return [{
                "entity_type": "CryptoWallet",
                "entity_value": addr.lower(),
                "metadata": {"source": "etherscan", "chain": "ethereum", "balance_eth": int(bal["result"]) / 1e18,
                             "recent_tx_hashes": [t.get("hash") for t in tx_list]},
                "confidence": 1.0,
                "reliability": 0.95,
            }]
        raise ValueError("INVALID_INPUT: crypto_recon supports Bitcoin (1..., 3..., bc1...) and Ethereum (0x...) addresses.")


registry.register(CryptoAdapter)
