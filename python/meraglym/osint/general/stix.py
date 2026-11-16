from typing import Any, Dict, List, Optional, Tuple

from meraglym.osint import BaseAdapter, registry

# STIX 2.1 Domain Objects -> MERAGLYM entity types (value taken from "name").
SDO_TYPES = {
    "threat-actor": ("ThreatActor", 0.9),
    "intrusion-set": ("ThreatActor", 0.9),
    "campaign": ("Campaign", 0.85),
    "malware": ("Malware", 0.85),
    "tool": ("Tool", 0.85),
    "attack-pattern": ("AttackPattern", 0.85),
    "vulnerability": ("Vulnerability", 0.9),
    "identity": ("Organization", 0.7),
    "infrastructure": ("Infrastructure", 0.8),
    "location": ("Location", 0.7),
    "indicator": ("Indicator", 0.8),
    "report": ("Report", 0.7),
}
# STIX Cyber-observables -> entity types (value taken from "value").
SCO_TYPES = {
    "ipv4-addr": "IPAddress",
    "ipv6-addr": "IPAddress",
    "domain-name": "Domain",
    "url": "URL",
    "email-addr": "Email",
    "mac-addr": "MACAddress",
    "autonomous-system": "ASN",
    "file": "File",
}
SKIP_TYPES = {"relationship", "sighting", "marking-definition", "bundle", "extension-definition", "language-content"}


def _sdo_value(obj: Dict[str, Any]) -> Optional[str]:
    name = obj.get("name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    if obj.get("type") == "vulnerability":
        for ref in obj.get("external_references") or []:
            if isinstance(ref, dict) and ref.get("external_id"):
                return str(ref["external_id"])
    if obj.get("type") == "indicator" and isinstance(obj.get("pattern"), str):
        return obj["pattern"][:500]
    return None


def _sco_value(obj: Dict[str, Any]) -> Optional[str]:
    if obj.get("type") == "autonomous-system" and obj.get("number") is not None:
        return f"AS{obj['number']}"
    if obj.get("type") == "file":
        hashes = obj.get("hashes") or {}
        for k in ("SHA-256", "SHA-1", "MD5"):
            if hashes.get(k):
                return str(hashes[k])
        return obj.get("name")
    v = obj.get("value")
    return str(v).strip() if v not in (None, "") else None


class StixAdapter(BaseAdapter):
    """STIX 2.1 import (e.g. MITRE ATT&CK / CTI bundles).

    Maps SDOs (threat actors, intrusion sets, malware, tools, attack patterns,
    vulnerabilities, indicators, ...) and SCOs (IPs, domains, URLs, emails,
    files, ASNs) into MERAGLYM observations. Relationships are attached to the
    source object's metadata. Unknown/unsupported types are counted, not fatal.
    """
    identifier = "stix_ingest"
    region = "GLOBAL"
    version = "2.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        stix_objects = payload.get("objects", [])
        if not isinstance(stix_objects, list):
            raise ValueError("INVALID_INPUT: STIX payload 'objects' must be a list.")
        if not stix_objects:
            raise ValueError("INVALID_INPUT: STIX payload must contain a non-empty 'objects' array.")

        by_id: Dict[str, Tuple[str, str]] = {}
        observations: List[Dict[str, Any]] = []
        skipped: Dict[str, int] = {}
        relationships = []

        for obj in stix_objects:
            if not isinstance(obj, dict) or not isinstance(obj.get("type"), str):
                skipped["invalid"] = skipped.get("invalid", 0) + 1
                continue
            stype = obj["type"]
            if stype == "relationship":
                relationships.append(obj)
                continue
            if stype in SKIP_TYPES or obj.get("revoked") or obj.get("x_mitre_deprecated"):
                continue
            if stype in SDO_TYPES:
                entity_type, confidence = SDO_TYPES[stype]
                value = _sdo_value(obj)
            elif stype in SCO_TYPES:
                entity_type, confidence = SCO_TYPES[stype], 0.9
                value = _sco_value(obj)
            else:
                skipped[stype] = skipped.get(stype, 0) + 1
                continue
            if not value:
                skipped[f"{stype}:no-value"] = skipped.get(f"{stype}:no-value", 0) + 1
                continue
            meta: Dict[str, Any] = {"stix_id": obj.get("id"), "stix_type": stype}
            for key in ("description", "aliases", "labels", "pattern", "valid_from", "first_seen",
                        "last_seen", "malware_types", "tool_types", "threat_actor_types", "kill_chain_phases"):
                if obj.get(key) not in (None, "", []):
                    v = obj[key]
                    meta[key] = v[:2000] if isinstance(v, str) else v
            refs = [r.get("external_id") or r.get("url") for r in obj.get("external_references") or []
                    if isinstance(r, dict) and (r.get("external_id") or r.get("url"))]
            if refs:
                meta["external_refs"] = refs[:20]
            observations.append({
                "source_identifier": self.identifier,
                "region": self.region,
                "entity_type": entity_type,
                "entity_value": value,
                "metadata": meta,
                "confidence": confidence,
            })
            if obj.get("id"):
                by_id[obj["id"]] = (entity_type, value)

        index = {o["metadata"].get("stix_id"): o for o in observations}
        for rel in relationships:
            src, tgt = index.get(rel.get("source_ref")), by_id.get(rel.get("target_ref"))
            if src and tgt:
                src["metadata"].setdefault("relationships", []).append(
                    {"type": rel.get("relationship_type"), "target_type": tgt[0], "target": tgt[1]}
                )
        if skipped and observations:
            observations[0]["metadata"]["stix_skipped"] = skipped
        return observations


registry.register(StixAdapter)
