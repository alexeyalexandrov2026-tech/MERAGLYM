"""Shared helpers for MERAGLYM OSINT adapters.

Error convention (the worker and the UI rely on these prefixes):

* ``EXTERNAL_DEPENDENCY_UNAVAILABLE: ...`` -- a required tool/library is not
  installed or not configured on this worker host.
* ``REQUIRES_USER_CREDENTIAL: ...`` -- an API key / session must be supplied.
* ``REQUIRES_EXTERNAL_SERVICE: ...`` -- the upstream service could not be
  reached (geo-blocking, outage, rate limit). For Russian state registries set
  ``RU_PROXY_URL`` (http://, https:// or socks5:// proxy located in RU).
* ``GEO_BLOCKED: ...`` -- a Russian registry refused/timed out and no
  ``RU_PROXY_URL`` is configured; retrying from this host will not help.

Errors with these prefixes (and ``ValueError`` for bad input) are permanent:
the worker marks the job FAILED immediately instead of retrying.
"""
from __future__ import annotations

import asyncio
import os
import shutil
import sys
from typing import Optional, Sequence

PERMANENT_ERROR_PREFIXES = (
    "EXTERNAL_DEPENDENCY_UNAVAILABLE",
    "REQUIRES_USER_CREDENTIAL",
    "INVALID_INPUT",
    "GEO_BLOCKED",
)


def dependency_error(msg: str) -> RuntimeError:
    return RuntimeError(f"EXTERNAL_DEPENDENCY_UNAVAILABLE: {msg}")


def credential_error(msg: str) -> RuntimeError:
    return RuntimeError(f"REQUIRES_USER_CREDENTIAL: {msg}")


def service_error(msg: str) -> RuntimeError:
    return RuntimeError(f"REQUIRES_EXTERNAL_SERVICE: {msg}")


def find_executable(name: str, env_var: Optional[str] = None) -> Optional[str]:
    """Return a path to ``name`` from ``env_var`` or ``PATH`` (or ``MERAGLYM_TOOLS_BIN``)."""
    if env_var:
        p = os.environ.get(env_var)
        if p and os.path.exists(p):
            return p
    extra = os.environ.get("MERAGLYM_TOOLS_BIN")
    if extra:
        found = shutil.which(name, path=extra)
        if found:
            return found
    return shutil.which(name)


def script_python(script_path: str, env_var: Optional[str] = None) -> str:
    """Interpreter for a script-based tool.

    Order: explicit ``<TOOL>_PYTHON`` env var, a ``.venv`` next to the script
    (or its parent), then the worker's own interpreter.
    """
    if env_var:
        p = os.environ.get(env_var)
        if p and os.path.exists(p):
            return p
    d = os.path.dirname(os.path.abspath(script_path))
    for base in (d, os.path.dirname(d)):
        cand = os.path.join(base, ".venv", "bin", "python")
        if os.path.exists(cand):
            return cand
    return sys.executable


async def run_tool(
    cmd: Sequence[str],
    *,
    timeout: float = 300,
    cwd: Optional[str] = None,
    env: Optional[dict] = None,
) -> tuple[int, str, str]:
    """Run an external tool without a shell; kill it on timeout."""
    full_env = os.environ.copy()
    full_env.update({"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "NO_COLOR": "1", "TERM": "dumb"})
    if env:
        full_env.update(env)
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
        env=full_env,
        start_new_session=True,
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        try:
            os.killpg(proc.pid, 9)
        except Exception:
            proc.kill()
        await proc.wait()
        raise service_error(f"{os.path.basename(cmd[0])} timed out after {int(timeout)}s")
    return proc.returncode or 0, out.decode("utf-8", "replace"), err.decode("utf-8", "replace")


def ru_http_client(timeout: float = 30.0, **kwargs):
    """httpx client for Russian state registries, routed via ``RU_PROXY_URL`` when set."""
    import httpx

    proxy = os.environ.get("RU_PROXY_URL") or None
    headers = kwargs.pop("headers", None) or {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    }
    return httpx.AsyncClient(timeout=timeout, proxy=proxy, headers=headers, follow_redirects=True, **kwargs)


def ru_service_error(source: str, exc: BaseException) -> RuntimeError:
    detail = f"{type(exc).__name__}: {str(exc)[:200]}"
    if not os.environ.get("RU_PROXY_URL"):
        return RuntimeError(
            f"GEO_BLOCKED: {source} is not reachable from this (non-RU) worker ({detail}). "
            "Set RU_PROXY_URL to an HTTP(S)/SOCKS5 proxy located in Russia."
        )
    return service_error(f"{source} unreachable via RU_PROXY_URL ({detail}).")


def require_str(payload: dict, key: str = "value", what: str = "value") -> str:
    v = payload.get(key)
    if not isinstance(v, str) or not v.strip():
        raise ValueError(f"INVALID_INPUT: '{key}' ({what}) is required.")
    return v.strip()


def require_inn(payload: dict) -> str:
    v = payload.get("value") or payload.get("inn")
    if not isinstance(v, str) or not v.strip().isdigit() or len(v.strip()) not in (10, 12):
        raise ValueError("INVALID_INPUT: 'value' (inn) must be a 10- or 12-digit INN.")
    return v.strip()
