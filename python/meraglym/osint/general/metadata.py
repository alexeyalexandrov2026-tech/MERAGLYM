import os
import tempfile
from typing import Any, Dict, List

from meraglym.osint import BaseAdapter, registry
from meraglym.osint._util import dependency_error, service_error

MAX_BYTES = 25 * 1024 * 1024
SKIP_TAGS = ("JPEGThumbnail", "TIFFThumbnail", "Filename", "EXIF MakerNote")


class MetadataAdapter(BaseAdapter):
    """EXIF / file metadata extraction (exifread) from an image URL or an uploaded file.

    'value' is an http(s) URL, or a file name inside METADATA_UPLOAD_DIR
    (default /opt/meraglym/uploads). Arbitrary server paths are rejected.
    """
    identifier = "metadata_extractor"
    region = "GLOBAL"
    version = "2.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        value = str(payload.get("value") or "").strip()
        if not value:
            raise ValueError("INVALID_INPUT: metadata_extractor requires an image URL or uploaded file name.")
        try:
            import exifread
        except ImportError:
            raise dependency_error("exifread not installed (pip install exifread).")
        tmp = None
        try:
            if value.startswith(("http://", "https://")):
                import httpx
                try:
                    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True,
                                                 headers={"User-Agent": "MERAGLYM-metadata/2.0"}) as client:
                        async with client.stream("GET", value) as r:
                            r.raise_for_status()
                            fd, tmp = tempfile.mkstemp(prefix="meta-")
                            size = 0
                            with os.fdopen(fd, "wb") as f:
                                async for chunk in r.aiter_bytes():
                                    size += len(chunk)
                                    if size > MAX_BYTES:
                                        raise ValueError("INVALID_INPUT: file larger than 25 MB.")
                                    f.write(chunk)
                            content_type = r.headers.get("content-type")
                except ValueError:
                    raise
                except Exception as e:
                    raise service_error(f"could not download {value}: {e}")
                path = tmp
            else:
                base = os.path.realpath(os.environ.get("METADATA_UPLOAD_DIR", "/opt/meraglym/uploads"))
                path = os.path.realpath(os.path.join(base, value))
                if not path.startswith(base + os.sep) or not os.path.isfile(path):
                    raise ValueError("INVALID_INPUT: file not found in the upload directory.")
                content_type = None
            with open(path, "rb") as f:
                tags = exifread.process_file(f, details=False)
            size = os.path.getsize(path)
        finally:
            if tmp and os.path.exists(tmp):
                os.remove(tmp)
        meta = {k: str(v)[:500] for k, v in tags.items() if k not in SKIP_TAGS}
        gps = {}
        try:
            def deg(v, ref):
                d, m, s = [float(x.num) / float(x.den) for x in v.values]
                x = d + m / 60 + s / 3600
                return -x if str(ref) in ("S", "W") else x
            if "GPS GPSLatitude" in tags and "GPS GPSLongitude" in tags:
                gps = {
                    "latitude": round(deg(tags["GPS GPSLatitude"], tags.get("GPS GPSLatitudeRef")), 6),
                    "longitude": round(deg(tags["GPS GPSLongitude"], tags.get("GPS GPSLongitudeRef")), 6),
                }
        except Exception:
            gps = {}
        obs = [{
            "entity_type": "File",
            "entity_value": value[:1000],
            "metadata": {"source": "exifread", "size_bytes": size, "content_type": content_type,
                         "tag_count": len(meta), "tags": meta, **({"gps": gps} if gps else {})},
            "confidence": 1.0,
            "reliability": 1.0,
        }]
        if gps:
            obs.append({
                "entity_type": "Location",
                "entity_value": f"{gps['latitude']},{gps['longitude']}",
                "metadata": {"source": "exif-gps", "file": value[:1000]},
                "confidence": 0.9,
                "reliability": 0.9,
            })
        return obs


registry.register(MetadataAdapter)
