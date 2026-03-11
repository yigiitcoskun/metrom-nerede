# -*- coding: utf-8 -*-
"""
tram-lines.json dosyasını okur (düzenlemez).
tram array'inden hat listesi (T1, T3, T4, T5...) ve her hattın stations/routes bilgisini verir.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

_BACKEND_DIR = Path(__file__).resolve().parent
# Vercel: JSON backend/ içinde; local: metrom-nerede/ kökünde
TRAM_LINES_PATH = _BACKEND_DIR / "tram-lines.json"
if not TRAM_LINES_PATH.exists():
    TRAM_LINES_PATH = _BACKEND_DIR.parent / "tram-lines.json"

_cache: Optional[Dict[str, Any]] = None


def _load() -> Dict[str, Any]:
    global _cache
    if _cache is not None:
        return _cache
    try:
        if TRAM_LINES_PATH.exists():
            with open(TRAM_LINES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data is not None:
                _cache = data
                return _cache
    except Exception:
        pass
    return {}


def get_tram_lines() -> List[Dict[str, Any]]:
    """tram-lines.json içindeki tram array'ini döner."""
    data = _load()
    return data.get("tram") or []


def get_line_by_code(code: str) -> Optional[Dict[str, Any]]:
    """Koda göre hat objesini döner (T1, T3, T4, T5 ...)."""
    code = (code or "").strip().upper()
    for line in get_tram_lines():
        if (line.get("code") or "").strip().upper() == code:
            return line
    return None


def get_stations_for_line(code: str) -> List[Dict[str, Any]]:
    """Hattın duraklarını döner: [ { stationId, name }, ... ]."""
    line = get_line_by_code(code)
    if not line:
        return []
    return line.get("stations") or []


def get_routes_for_line(code: str) -> List[Dict[str, Any]]:
    """Hattın yönlerini (route) döner: [ { routeId, name }, ... ]."""
    line = get_line_by_code(code)
    if not line:
        return []
    return line.get("routes") or []


def get_station_id(line_code: str, station_name: str) -> Optional[int]:
    """Hattaki durak adına göre stationId döner."""
    stations = get_stations_for_line(line_code)
    name_clean = _normalize(station_name)
    for s in stations:
        n = (s.get("name") or "").strip()
        if n == station_name or _normalize(n) == name_clean:
            return s.get("stationId")
        if name_clean in _normalize(n) or _normalize(n) in name_clean:
            return s.get("stationId")
    return None


def _normalize(s: str) -> str:
    if not s:
        return ""
    return "".join(c.lower() for c in s if c.isalnum() or c in " -").strip()
