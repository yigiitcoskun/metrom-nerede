# -*- coding: utf-8 -*-
"""
Metro İstanbul canlı sefer verisi: AJAXSeferGetir proxy.
Form-data: secim=1, saat="", dakika="", tarih1="", tarih2=DD.MM.YYYY, station, route, kod.
station/route: metrom-nerede/metro-lines.json içindeki metro array'inden (line code + stations/routes).
"""
import re
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests

from veriler_loader import get_line_by_code, get_station_id, get_routes_for_line
from tram_loader import get_station_id as get_tram_station_id, get_routes_for_line as get_tram_routes_for_line

METRO_PAGE_URL = "https://www.metro.istanbul/SeferDurumlari/SeferDetaylari"
METRO_AJAX_URL = "https://www.metro.istanbul/SeferDurumlari/AJAXSeferGetir"
CACHE_TTL_SECONDS = 45
META_CACHE_TTL = 6 * 3600
RATE_LIMIT_PER_MINUTE = 30
DEFAULT_KOD = "5648760e-9d58-457d-aa52-370d094677f0"

# metro-lines.json'da yoksa (eski M7 vb.) sayfa scrape / fallback
FALLBACK_M7_STATIONS: Dict[str, str] = {"Yenimahalle": "155"}
FALLBACK_M7_ROUTES: Dict[str, str] = {
    "Mahmutbey": "41",
    "Yıldız": "42",
    "Yıldız (Mecidiyeköy)": "42",
    "Mecidiyeköy": "42",
}

_meta_cache: Dict[str, Any] = {"kod": None, "expires": 0, "stations": {}, "routes": {}}
_response_cache: Dict[Tuple[str, str, str], Tuple[List[Dict], float]] = {}
_response_cache_by_ids: Dict[Tuple[str, str], Tuple[Dict[str, Any], float]] = {}
_rate_limit: Dict[str, List[float]] = defaultdict(list)


def _normalize(s: str) -> str:
    if not s:
        return ""
    return "".join(c.lower() for c in s if c.isalnum() or c in " -").strip()


def _fetch_page() -> str:
    r = requests.get(METRO_PAGE_URL, timeout=10, headers={"User-Agent": "MetroMNerede/1.0"})
    r.raise_for_status()
    return r.text


def _extract_kod(html: str) -> str:
    m = re.search(r'formData\.append\s*\(\s*["\']kod["\']\s*,\s*["\']([^"\']+)["\']\s*\)', html)
    if m:
        return m.group(1).strip()
    m = re.search(r'"kod"\s*:\s*["\']([^"\']+)["\']', html)
    if m:
        return m.group(1).strip()
    return DEFAULT_KOD


def _extract_select_options(html: str, select_id: str) -> List[Tuple[str, str]]:
    pat = rf'<select[^>]*id=["\']{re.escape(select_id)}["\'][^>]*>(.*?)</select>'
    m = re.search(pat, html, re.DOTALL | re.IGNORECASE)
    if not m:
        return []
    body = m.group(1)
    options = re.findall(r'<option\s+value=["\']([^"\']*)["\'][^>]*>([^<]*)</option>', body, re.IGNORECASE)
    return [(v.strip(), _strip(lbl)) for v, lbl in options]


def _strip(s: str) -> str:
    return (s or "").strip()


def get_metro_meta(force_refresh: bool = False) -> Dict[str, Any]:
    """Sayfadan kod ve mümkünse station/route listelerini al. Cache'li."""
    now = time.time()
    if not force_refresh and _meta_cache.get("expires", 0) > now:
        return {"kod": _meta_cache.get("kod") or DEFAULT_KOD, "stations": _meta_cache.get("stations", {}), "routes": _meta_cache.get("routes", {})}
    try:
        html = _fetch_page()
        kod = _extract_kod(html)
        _meta_cache["kod"] = kod
        _meta_cache["expires"] = now + META_CACHE_TTL
        # M7 için select id'leri farklı olabilir; deneyebiliriz
        for sid in ("istasyonlar_7", "istasyonlar_3", "station"):
            opts = _extract_select_options(html, sid)
            if opts:
                _meta_cache.setdefault("stations", {})["M7"] = opts
                break
        for rid in ("seferler_7", "seferler_3", "route"):
            opts = _extract_select_options(html, rid)
            if opts:
                _meta_cache.setdefault("routes", {})["M7"] = opts
                break
    except Exception:
        pass
    return {
        "kod": _meta_cache.get("kod") or DEFAULT_KOD,
        "stations": _meta_cache.get("stations", {}),
        "routes": _meta_cache.get("routes", {}),
    }


def _get_station_id_any(hat: str, istasyon: str) -> Optional[int]:
    """Önce metro, yoksa tram (tram-lines.json)."""
    sid = get_station_id(hat, istasyon)
    if sid is not None:
        return sid
    return get_tram_station_id(hat, istasyon)


def _get_routes_for_line_any(hat: str) -> List[Dict[str, Any]]:
    """Önce metro, yoksa tram."""
    routes = get_routes_for_line(hat)
    if routes:
        return routes
    return get_tram_routes_for_line(hat)


def _resolve_station_id(hat: str, istasyon: str) -> Optional[str]:
    # 1) metro-lines.json veya tram-lines.json
    sid = _get_station_id_any(hat, istasyon)
    if sid is not None:
        return str(sid)
    # 2) Sayfa scrape (get_metro_meta)
    meta = get_metro_meta()
    stations = meta.get("stations", {}).get(hat, [])
    ist_norm = _normalize(istasyon)
    for sid, name in stations:
        if sid and _normalize(name) == ist_norm:
            return sid
    for sid, name in stations:
        if sid and (ist_norm in _normalize(name) or _normalize(name) in ist_norm):
            return sid
    # 3) Hardcoded fallback
    if hat.upper() == "M7":
        for name, sid in FALLBACK_M7_STATIONS.items():
            if _normalize(name) == ist_norm or ist_norm in _normalize(name):
                return sid
    return None


def _resolve_route_id(hat: str, yon: str) -> Optional[str]:
    # 1) metro veya tram routes[].name "A → B" içinde yon eşleşmesi
    routes = _get_routes_for_line_any(hat)
    yon_norm = _normalize(yon)
    for r in routes:
        rid = r.get("routeId")
        name = (r.get("name") or "").strip()
        if not rid:
            continue
        nnorm = _normalize(name)
        if yon_norm == nnorm or yon_norm in nnorm or nnorm in yon_norm:
            return str(rid)
        # "Yenikapı → Atatürk Havalimanı" -> Yenikapı veya Atatürk Havalimanı ile eşleş
        for part in name.split("→"):
            if _normalize(part) == yon_norm:
                return str(rid)
    # 2) Sayfa scrape
    meta = get_metro_meta()
    route_list = meta.get("routes", {}).get(hat, [])
    for rid, label in route_list:
        if rid and (yon_norm in _normalize(label) or _normalize(label) in yon_norm):
            return rid
    # 3) Hardcoded fallback
    if hat.upper() == "M7":
        for name, rid in FALLBACK_M7_ROUTES.items():
            if _normalize(name) == yon_norm or yon_norm in _normalize(name):
                return rid
    return None


def _get_kod() -> str:
    """Kod: sayfa scrape veya DEFAULT_KOD."""
    meta = get_metro_meta()
    return (meta.get("kod") or DEFAULT_KOD) or DEFAULT_KOD


def sefer_getir_by_ids(
    station_id: str,
    route_id: str,
    kod: Optional[str] = None,
    yon_label: Optional[str] = None,
) -> Dict[str, Any]:
    """
    AJAXSeferGetir'e birebir form: secim=1, saat="", dakika="", tarih1="", tarih2=bugün, station, route, kod.
    Returns: { kaynak, seferler: [ { yon, zaman, minutes } ], hata? }
    """
    kod = (kod or _get_kod()).strip()
    tarih2 = datetime.now().strftime("%d.%m.%Y")
    payload = {
        "secim": "1",
        "saat": "",
        "dakika": "",
        "tarih1": "",
        "tarih2": tarih2,
        "station": station_id,
        "route": route_id,
        "kod": kod,
    }
    headers = {"X-Requested-With": "XMLHttpRequest", "User-Agent": "MetroMNerede/1.0"}
    try:
        r = requests.post(METRO_AJAX_URL, data=payload, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return {"kaynak": "metro_istanbul", "seferler": [], "hata": str(e)}

    raw_list = data.get("sefer") or []
    seferler = []
    for s in raw_list:
        zaman = (s.get("zaman") or "").strip()
        durak2 = (s.get("durak2") or s.get("yon") or (yon_label or "")).strip()
        minutes = _zaman_to_minutes(zaman)
        seferler.append({"yon": durak2, "zaman": zaman, "minutes": minutes})
    return {"kaynak": "metro_istanbul", "seferler": seferler}


def _zaman_to_minutes(zaman: str) -> Optional[int]:
    """'12:16' -> şimdiki saatten kaç dk sonra."""
    if not zaman or len(zaman) < 5:
        return None
    try:
        h, m = int(zaman[0:2]), int(zaman[3:5])
    except ValueError:
        return None
    now = datetime.now()
    target_min = h * 60 + m
    now_min = now.hour * 60 + now.minute
    delta = target_min - now_min
    if delta < -60:
        delta += 24 * 60
    if delta < 0:
        return 0
    return delta


def sefer_getir(hat: str, istasyon: str, yon: str) -> Dict[str, Any]:
    """
    Metro İstanbul canlı sefer listesi.
    hat: M7, istasyon: Yenimahalle, yon: Mahmutbey veya Yıldız (Mecidiyeköy).
    Returns: { kaynak, seferler: [ { yon, zaman, minutes } ], hata? }
    """
    station_id = _resolve_station_id(hat, istasyon)
    route_id = _resolve_route_id(hat, yon)
    if not station_id or not route_id:
        return {
            "kaynak": "metro_istanbul",
            "seferler": [],
            "hata": "istasyon veya yön bulunamadı",
            "station_id": station_id,
            "route_id": route_id,
        }
    return sefer_getir_by_ids(station_id, route_id, yon_label=yon)


def sefer_getir_cached(hat: str, istasyon: str, yon: str) -> Dict[str, Any]:
    """Cache'li sefer getir. Aynı (hat, istasyon, yon) için CACHE_TTL saniye cache."""
    key = (hat.upper(), _normalize(istasyon), _normalize(yon))
    now = time.time()
    if key in _response_cache:
        cached, ts = _response_cache[key]
        if now - ts < CACHE_TTL_SECONDS:
            return cached
    result = sefer_getir(hat, istasyon, yon)
    _response_cache[key] = (result, now)
    return result


def sefer_getir_iki_yon(hat: str, istasyon: str, yon1: str = "", yon2: str = "") -> Dict[str, Any]:
    """
    İki yön için seferleri getir. metro-lines.json'da hat varsa stationId + 2 route ile istek atar;
    yoksa yon1/yon2 ile (M7 vb.) resolve eder.
    Returns: { kaynak, istasyon, hat, yonler: [ { yon, minutes, seferler } ], hata? }
    """
    station_id = _get_station_id_any(hat, istasyon)
    routes = _get_routes_for_line_any(hat) if station_id is not None else []
    if station_id is not None and len(routes) >= 1:
        # metro-lines.json veya tram-lines.json: her route için bir istek
        yonler = []
        for route in routes:
            rid = route.get("routeId")
            rname = (route.get("name") or "").strip()
            if rid is None:
                continue
            key = (str(station_id), str(rid))
            now = time.time()
            if key in _response_cache_by_ids:
                cached, ts = _response_cache_by_ids[key]
                if now - ts < CACHE_TTL_SECONDS:
                    res = cached
                else:
                    res = sefer_getir_by_ids(str(station_id), str(rid), yon_label=rname)
                    _response_cache_by_ids[key] = (res, now)
            else:
                res = sefer_getir_by_ids(str(station_id), str(rid), yon_label=rname)
                _response_cache_by_ids[key] = (res, now)
            seferler = res.get("seferler") or []
            first_min = seferler[0]["minutes"] if seferler else None
            yonler.append({"yon": rname, "minutes": first_min, "seferler": seferler})
        return {
            "kaynak": "metro_istanbul",
            "istasyon": istasyon,
            "hat": hat,
            "yonler": yonler,
            "hata": None,
        }
    # Fallback: yon1, yon2 ile (M7 vb.)
    r1 = sefer_getir_cached(hat, istasyon, yon1 or "Mahmutbey")
    r2 = sefer_getir_cached(hat, istasyon, yon2 or "Yıldız (Mecidiyeköy)")
    yonler = []
    for r, yon_label in [(r1, yon1 or "Mahmutbey"), (r2, yon2 or "Yıldız (Mecidiyeköy)")]:
        seferler = r.get("seferler") or []
        first_min = seferler[0]["minutes"] if seferler else None
        yonler.append({"yon": yon_label, "minutes": first_min, "seferler": seferler})
    return {
        "kaynak": "metro_istanbul",
        "istasyon": istasyon,
        "hat": hat,
        "yonler": yonler,
        "hata": r1.get("hata") or r2.get("hata"),
    }


def check_rate_limit(ip: str) -> bool:
    """True = istek yapılabilir, False = limit aşıldı."""
    now = time.time()
    window = 60
    times = _rate_limit[ip]
    times[:] = [t for t in times if now - t < window]
    if len(times) >= RATE_LIMIT_PER_MINUTE:
        return False
    times.append(now)
    return True
