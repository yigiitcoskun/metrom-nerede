# -*- coding: utf-8 -*-
"""Load GTFS from csvs CSV files and build in-memory structures for API."""
import csv
from pathlib import Path
from datetime import datetime, time, timedelta
from collections import defaultdict

from config import (
    GTFS_CSV_DIR,
    METRO_SHORT_NAMES,
    TRAM_SHORT_NAMES,
    MARMARAY_SHORT_NAMES,
    SIGNATURE_STOPS,
)


def _find_csv(keywords: list) -> Path:
    """Find CSV in GTFS_CSV_DIR whose filename contains any keyword."""
    for p in Path(GTFS_CSV_DIR).iterdir():
        if p.suffix.upper() != ".CSV":
            continue
        name = p.name.upper()
        for kw in keywords:
            if kw.upper() in name:
                return p
    return None


def _open_csv(name_or_keywords):
    if isinstance(name_or_keywords, str):
        name_or_keywords = [name_or_keywords]
    path = None
    for n in name_or_keywords:
        p = GTFS_CSV_DIR / n
        if p.exists():
            path = p
            break
    if path is None:
        path = _find_csv(["rota", "route"])
    if path is None and any("urak" in str(x).lower() or "stop" in str(x).lower() for x in name_or_keywords):
        path = _find_csv(["durak", "stops"])
    if path is None and any("zaman" in str(x).lower() or "time" in str(x).lower() for x in name_or_keywords):
        path = _find_csv(["zaman", "time"])
    if not path or not path.exists():
        raise FileNotFoundError(f"CSV not found: {name_or_keywords} in {GTFS_CSV_DIR}")
    for enc in ("utf-8", "cp1254", "iso-8859-9"):
        try:
            with open(path, "r", encoding=enc, errors="replace") as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def _parse_time(s: str):
    """Parse HH:MM:SS to seconds since midnight. GTFS allows 25:00 = 01:00 next day."""
    if not s or s.strip() == "":
        return None
    parts = s.strip().split(":")
    if len(parts) < 2:
        return None
    try:
        h, m = int(parts[0]), int(parts[1])
        sec = int(parts[2]) if len(parts) > 2 else 0
        secs = h * 3600 + m * 60 + sec
        # GTFS: times >= 24:00 mean next day
        if secs >= 24 * 3600:
            secs -= 24 * 3600
        return secs
    except (ValueError, IndexError):
        return None


def _seconds_to_minutes(secs: int) -> int:
    if secs is None or secs < 0:
        return None
    return secs // 60


def load_routes():
    """Load routes and filter by metro/tram/marmaray short names."""
    rows = _open_csv(["İBB Rotaları.csv", "*Rota*.csv", "*outes*.csv"])
    if not rows:
        # try alternative name
        for fname in Path(GTFS_CSV_DIR).glob("*.csv"):
            if "rot" in fname.name.lower() or "route" in fname.name.lower():
                with open(fname, "r", encoding="utf-8", errors="replace") as f:
                    rows = list(csv.DictReader(f))
                break
    routes = []
    for r in rows:
        short = (r.get("route_short_name") or "").strip().upper()
        short = short.replace("İ", "I").replace("I", "İ")  # normalize
        raw_short = (r.get("route_short_name") or "").strip()
        short_upper = short.upper().replace("İ", "I")
        allowed = {s.upper().replace("İ", "I") for s in METRO_SHORT_NAMES | TRAM_SHORT_NAMES | MARMARAY_SHORT_NAMES}
        if short_upper in allowed or short in METRO_SHORT_NAMES or short in TRAM_SHORT_NAMES or short in MARMARAY_SHORT_NAMES:
            routes.append({
                "route_id": r.get("route_id", "").strip(),
                "route_short_name": raw_short,
                "route_long_name": (r.get("route_long_name") or "").strip(),
            })
    return routes


def load_stops():
    """Load all stops as dict stop_id -> {stop_id, stop_name, stop_url, ...}."""
    rows = _open_csv(["Duraklar.csv", "*uraklar*.csv"])
    key = "stop_id"
    return {r.get(key, "").strip(): r for r in rows if r.get(key)}


def build_route_official_stops(routes: list, stops: dict) -> dict:
    """
    From Duraklar, stops with stop_url containing hat=M7, hat=M2 etc. belong to that line.
    Returns route_id -> set of stop_ids (official stations for that route).
    """
    route_short_by_id = {r["route_id"]: r["route_short_name"].upper() for r in routes}
    result = defaultdict(set)
    for stop_id, row in stops.items():
        url = (row.get("stop_url") or "").strip()
        if "hat=" not in url and "HatDetay" not in url:
            continue
        url_upper = url.upper()
        for route_id, short in route_short_by_id.items():
            if "HAT=" + short in url_upper or "HAT=" + short.replace("İ", "I") in url_upper:
                result[route_id].add(stop_id)
                break
    return dict(result)


def load_frequencies():
    """Load frequencies: list of (trip_id, start_secs, end_secs, headway_secs). end_secs can be 24*3600 for 24:00."""
    try:
        rows = _open_csv(["Frekanslar.csv", "*rekans*.csv", "*requenc*.csv"])
    except FileNotFoundError:
        return []
    out = []
    for r in rows:
        trip_id = (r.get("trip_id") or "").strip()
        start_secs = _parse_time(r.get("start_time") or "")
        end_raw = (r.get("end_time") or "").strip()
        if end_raw and "24:00" in end_raw:
            end_secs = 24 * 3600
        else:
            end_secs = _parse_time(end_raw)
            if end_secs is not None and end_secs == 0 and "24" in end_raw:
                end_secs = 24 * 3600
        headway = int(r.get("headway_secs") or 0)
        if not trip_id or start_secs is None or end_secs is None or headway <= 0:
            continue
        out.append((trip_id, start_secs, end_secs, headway))
    return out


def load_stop_times():
    """Load stop_times; return list of (trip_id, arrival_secs, departure_secs, stop_id, stop_sequence, stop_headsign)."""
    rows = _open_csv(["Durak Zamanları.csv", "*Zaman*.csv"])
    out = []
    for r in rows:
        trip_id = (r.get("trip_id") or "").strip()
        stop_id = (r.get("stop_id") or "").strip()
        arr = _parse_time(r.get("arrival_time") or r.get("arrival_time"))
        dep = _parse_time(r.get("departure_time") or r.get("departure_time"))
        seq = int(r.get("stop_sequence") or 0)
        headsign = (r.get("stop_headsign") or "").strip()
        if not trip_id or not stop_id:
            continue
        out.append((trip_id, arr, dep, stop_id, seq, headsign))
    return out


def build_trip_to_route(routes_by_short: dict, stops: dict, stop_times: list, route_official_stops: dict) -> dict:
    """
    Build mapping trip_id -> route_id.
    Prefer: trip has many stops in route's official set (from stop_url hat=M7 etc).
    Fallback: signature + keyword match as before.
    """
    # Official stops: route_id -> set of stop_ids (from Duraklar stop_url)
    route_id_to_short = {r["route_id"]: short for short, r in routes_by_short.items()}

    # trip_id -> set of stop_ids
    trip_stops = defaultdict(set)
    for t, _a, _d, stop_id, _seq, _h in stop_times:
        trip_stops[t].add(stop_id)

    trip_to_route = {}
    for trip_id, stop_set in trip_stops.items():
        assigned = False
        # First try: assign to route where this trip has the most official stops (and at least 4)
        best_route = None
        best_count = 3
        for route_id, official in route_official_stops.items():
            if not official:
                continue
            overlap = len(stop_set & official)
            if overlap >= 4 and overlap > best_count:
                best_count = overlap
                best_route = route_id
        if best_route is not None:
            trip_to_route[trip_id] = best_route
            assigned = True

        if assigned:
            continue
        # Fallback: keyword + signature match (original logic)
        stop_names = {sid: (stops.get(sid) or {}).get("stop_name") or "" for sid in stop_set}
        trip_names = " ".join(stop_names.values()).upper().replace("İ", "I")
        for short, route_info in routes_by_short.items():
            route_id = route_info["route_id"]
            if route_id in route_official_stops and route_official_stops[route_id]:
                sig_stops = route_official_stops[route_id]
            else:
                sig_stops = set()
                long_name = (route_info.get("route_long_name") or "").upper().replace("İ", "I")
                for sid, name in stop_names.items():
                    if name and (short.upper() in name.upper() or any(p in (name or "").upper() for p in long_name.split("-")[:2])):
                        sig_stops.add(sid)
            if not sig_stops or not (sig_stops & stop_set):
                continue
            keywords = [p.strip().upper().replace("İ", "I") for p in (route_info.get("route_long_name") or "").split("-") if p.strip()]
            matches = sum(1 for kw in keywords if kw and kw in trip_names)
            if matches >= 2 and 4 <= len(stop_set) <= 50:
                trip_to_route[trip_id] = route_id
                break
    return trip_to_route


def get_now_seconds():
    """Current time as seconds since midnight (local)."""
    now = datetime.now().time()
    return now.hour * 3600 + now.minute * 60 + now.second


def _format_minutes_display(minutes: int) -> str:
    """Format minutes for display: cap at 120, show '>2 saat' or time."""
    if minutes is None or minutes < 0:
        return None
    if minutes <= 120:
        return None  # API returns minutes as-is
    if minutes < 1440:  # < 24h
        return f">{minutes // 60} saat"
    return "Yarın"


def _trip_destination_stop_id(trip_id: str, stop_times: list) -> str:
    """Return the last stop_id of the trip (destination)."""
    rows = [(seq, sid) for tid, _a, _d, sid, seq, _h in stop_times if tid == trip_id]
    if not rows:
        return ""
    rows.sort(key=lambda x: x[0], reverse=True)
    return rows[0][1]


def _normalize_direction_for_route(
    route_id: str,
    route_station_ids: list,
    stops: dict,
    trip_to_route: dict,
    stop_times: list,
) -> dict:
    """
    Map trip_id -> display direction label (one of two line ends).
    So we show "Yıldız (Mecidiyeköy) yönü" / "Mahmutbey yönü" instead of "Yenimahalle yönü".
    """
    if not route_station_ids or len(route_station_ids) < 2:
        return {}
    first_id = route_station_ids[0]
    last_id = route_station_ids[-1]
    first_name = (stops.get(first_id) or {}).get("stop_name") or "A"
    last_name = (stops.get(last_id) or {}).get("stop_name") or "B"
    # M7: show "Yıldız (Mecidiyeköy)" for clarity
    if last_name and ("yıldız" in last_name.lower() or "yildiz" in last_name.lower()):
        last_name = "Yıldız (Mecidiyeköy)"
    if first_name and "mahmutbey" in first_name.lower():
        first_name = "Mahmutbey"
    trip_ids = [t for t, rid in trip_to_route.items() if rid == route_id]
    out = {}
    for t in trip_ids:
        dest_id = _trip_destination_stop_id(t, stop_times)
        if dest_id == first_id:
            out[t] = first_name
        elif dest_id == last_id:
            out[t] = last_name
        else:
            # Map by position: if dest is in first half of route -> towards first, else towards last
            try:
                idx = route_station_ids.index(dest_id)
            except ValueError:
                out[t] = last_name
                continue
            if idx < len(route_station_ids) / 2:
                out[t] = first_name
            else:
                out[t] = last_name
    return out


def _next_departures_from_frequencies(
    stop_id: str,
    route_id: str,
    trip_to_route: dict,
    stop_times: list,
    frequencies: list,
    now_secs: int,
) -> list:
    """
    For trips that have frequency (headway), compute next departure at this stop.
    Returns list of (minutes_sec, trip_id).
    """
    day_secs = 24 * 3600
    # trip_id -> min arrival_secs (first stop)
    trip_base = {}
    # (trip_id, stop_id) -> arrival_secs at that stop
    trip_stop_arrival = {}
    for trip_id, arr, _d, sid, _seq, _h in stop_times:
        if arr is None:
            continue
        if trip_id not in trip_base or arr < trip_base[trip_id]:
            trip_base[trip_id] = arr
        if sid == stop_id:
            trip_stop_arrival[(trip_id, sid)] = arr

    # frequencies: (trip_id, start_secs, end_secs, headway_secs)
    freq_by_trip = defaultdict(list)
    for trip_id, start_s, end_s, headway in frequencies:
        if trip_to_route.get(trip_id) != route_id:
            continue
        freq_by_trip[trip_id].append((start_s, end_s, headway))

    out = []
    for (trip_id, sid), stop_arr in trip_stop_arrival.items():
        if sid != stop_id:
            continue
        base = trip_base.get(trip_id)
        if base is None:
            continue
        offset = stop_arr - base
        for start_s, end_s, headway in freq_by_trip.get(trip_id, []):
            if headway <= 0:
                continue
            w_start = start_s + offset
            w_end = end_s + offset
            if now_secs > w_end:
                # next day first departure
                minutes_sec = (day_secs - now_secs) + w_start
                out.append((minutes_sec, trip_id))
                continue
            if now_secs <= w_start:
                t = w_start
            else:
                k = (now_secs - w_start + headway - 1) // headway
                t = w_start + k * headway
                if t > w_end:
                    minutes_sec = (day_secs - now_secs) + w_start
                    out.append((minutes_sec, trip_id))
                    continue
            out.append((t - now_secs, trip_id))
    return out


def get_next_departures_for_stop(
    stop_id: str,
    route_id: str,
    trip_to_route: dict,
    stop_times: list,
    now_secs: int,
    max_next: int = 5,
    route_station_ids: list = None,
    stops: dict = None,
    frequencies: list = None,
):
    """
    Return next departures per direction. Direction = line terminus (Yıldız / Mahmutbey),
    not intermediate stop name. Uses both fixed stop_times and frequency-based trips.
    """
    day_secs = 24 * 3600
    candidates = []
    for trip_id, arr, dep, sid, seq, headsign in stop_times:
        if sid != stop_id or trip_to_route.get(trip_id) != route_id:
            continue
        if dep is None:
            dep = arr
        if dep is None:
            continue
        if dep >= now_secs:
            candidates.append((dep - now_secs, trip_id))
        else:
            candidates.append((day_secs - now_secs + dep, trip_id))

    # Add frequency-based next departures (M7 etc. run every 6 min)
    if frequencies:
        freq_candidates = _next_departures_from_frequencies(
            stop_id, route_id, trip_to_route, stop_times, frequencies, now_secs
        )
        candidates.extend(freq_candidates)

    candidates.sort(key=lambda x: x[0])

    # Normalize to 2 directions (line endpoints)
    direction_label_by_trip = {}
    if route_station_ids and stops:
        direction_label_by_trip = _normalize_direction_for_route(
            route_id, route_station_ids, stops, trip_to_route, stop_times
        )

    by_direction = {}
    for minutes_sec, trip_id in candidates:
        label = direction_label_by_trip.get(trip_id)
        if not label:
            label = "Yön"
        if label not in by_direction or minutes_sec < by_direction[label]:
            by_direction[label] = minutes_sec

    out = []
    for d, sec in sorted(by_direction.items(), key=lambda x: x[1])[:max_next]:
        mins = _seconds_to_minutes(sec)
        display = None
        if mins is not None and mins > 120:
            display = _format_minutes_display(mins)
            mins = min(mins, 120)
        out.append({"direction": d, "minutes": mins, "display": display})
    return out


def get_routes_by_type(routes: list) -> dict:
    """Split routes into metrolar, tramvaylar, marmaray."""
    metrolar = [r for r in routes if (r.get("route_short_name") or "").upper() in METRO_SHORT_NAMES]
    tramvaylar = [r for r in routes if (r.get("route_short_name") or "").upper() in TRAM_SHORT_NAMES]
    marmaray = [r for r in routes if (r.get("route_short_name") or "").upper() in MARMARAY_SHORT_NAMES]
    return {"metrolar": metrolar, "tramvaylar": tramvaylar, "marmaray": marmaray}


def get_stops_for_route(
    route_id: str,
    trip_to_route: dict,
    stop_times: list,
    stops: dict,
    route_official_stops: dict = None,
) -> list:
    """
    Get ordered list of stops for a route.
    If route_official_stops is given, only return stops in that set (correct metro stations).
    """
    official = (route_official_stops or {}).get(route_id) or set()
    trip_ids_for_route = [t for t, rid in trip_to_route.items() if rid == route_id]
    if not trip_ids_for_route:
        return []
    # Pick a trip that has the most official stops (so order is correct)
    best_trip = None
    best_official_count = -1
    for t in trip_ids_for_route:
        seq_stops = [(seq, sid) for tid, _a, _d, sid, seq, _h in stop_times if tid == t]
        seq_stops.sort(key=lambda x: x[0])
        if official:
            official_in_trip = sum(1 for _seq, sid in seq_stops if sid in official)
            if official_in_trip > best_official_count and official_in_trip >= 2:
                best_official_count = official_in_trip
                best_trip = seq_stops
        elif not best_trip or len(seq_stops) < len(best_trip):
            best_trip = seq_stops
    if not best_trip:
        return []
    seen = set()
    out = []
    for _seq, sid in best_trip:
        if sid in seen:
            continue
        if official and sid not in official:
            continue
        seen.add(sid)
        name = (stops.get(sid) or {}).get("stop_name") or sid
        out.append({"stop_id": sid, "stop_name": name})
    return out


class GTFSStore:
    """In-memory store built from CSV."""

    def __init__(self):
        self.routes = []
        self.stops = {}
        self.stop_times = []
        self.trip_to_route = {}
        self.routes_by_short = {}
        self.routes_by_id = {}
        self.route_official_stops = {}
        self.frequencies = []

    def load(self):
        self.routes = load_routes()
        self.stops = load_stops()
        self.stop_times = load_stop_times()
        self.frequencies = load_frequencies()
        self.routes_by_short = {r["route_short_name"].upper(): r for r in self.routes}
        self.routes_by_id = {r["route_id"]: r for r in self.routes}
        self.route_official_stops = build_route_official_stops(self.routes, self.stops)
        self.trip_to_route = build_trip_to_route(
            self.routes_by_short, self.stops, self.stop_times, self.route_official_stops
        )
        return self

    def get_categories(self):
        return get_routes_by_type(self.routes)

    def get_stations_for_route(self, route_id: str):
        return get_stops_for_route(
            route_id, self.trip_to_route, self.stop_times, self.stops, self.route_official_stops
        )

    def get_arrivals(self, route_id: str, stop_id: str):
        now = get_now_seconds()
        stations = self.get_stations_for_route(route_id)
        route_station_ids = [s["stop_id"] for s in stations]
        return get_next_departures_for_stop(
            stop_id,
            route_id,
            self.trip_to_route,
            self.stop_times,
            now,
            max_next=5,
            route_station_ids=route_station_ids,
            stops=self.stops,
            frequencies=self.frequencies,
        )


_store = None


def get_store() -> GTFSStore:
    global _store
    if _store is None:
        _store = GTFSStore().load()
    return _store
