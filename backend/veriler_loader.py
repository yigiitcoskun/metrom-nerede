# -*- coding: utf-8 -*-
"""
metro-lines.json dosyasını okur (düzenlemez).
metro array'inden hat listesi (M1A, M1B, M2...) ve her hattın stations/routes bilgisini verir.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

_BACKEND_DIR = Path(__file__).resolve().parent
# Vercel: JSON backend/ içinde; local: metrom-nerede/ kökünde
VERILER_JSON_PATH = _BACKEND_DIR / "metro-lines.json"
if not VERILER_JSON_PATH.exists():
    VERILER_JSON_PATH = _BACKEND_DIR.parent / "metro-lines.json"

_cache: Optional[Dict[str, Any]] = None


def _load() -> Dict[str, Any]:
    global _cache
    if _cache is not None:
        return _cache
    try:
        if VERILER_JSON_PATH.exists():
            with open(VERILER_JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data is not None:
                _cache = data
                return _cache
    except Exception:
        pass
    # Hata/boş dosyada önbelleğe boş yazma; bir sonraki istekte tekrar dene
    return {}


def get_metro_lines() -> List[Dict[str, Any]]:
    """metro-lines.json içindeki metro array'ini döner. Her öğe: { lineId, code, name, routes, stations, routeStationMap }."""
    data = _load()
    return data.get("metro") or []


def get_line_by_code(code: str) -> Optional[Dict[str, Any]]:
    """Koda göre hat objesini döner (M1A, M1B, M2 ...)."""
    code = (code or "").strip().upper()
    for line in get_metro_lines():
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
    """Hattın yönlerini (route) döner: [ { routeId, name }, ... ] (örn. 2 yön)."""
    line = get_line_by_code(code)
    if not line:
        return []
    return line.get("routes") or []


def get_station_id(line_code: str, station_name: str) -> Optional[int]:
    """Hattaki durak adına göre stationId döner (eşleşme: tam veya normalize)."""
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
