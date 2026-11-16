from .registry import registry, AdapterRegistry
from .base import BaseAdapter
from .cis import *  # noqa: F401,F403  (importing registers the adapters)
from .general import *  # noqa: F401,F403

ALL_ADAPTER_IDENTIFIERS = (
    # CIS / Russian registries
    "egrul_registry", "rfsd_financials", "efrsb_bankruptcy", "fns_tax", "fssp_check",
    "kad_arbitr", "sudrf_courts", "mvd_wanted",
    # Global
    "stix_ingest", "email_recon", "holehe_recon", "social_recon", "geospatial_mapper",
    "metadata_extractor", "crypto_recon", "camera_recon", "darkweb_mapper",
    "spiderfoot_meta", "opencti_connector",
)

__all__ = ["registry", "AdapterRegistry", "BaseAdapter", "ALL_ADAPTER_IDENTIFIERS"]
