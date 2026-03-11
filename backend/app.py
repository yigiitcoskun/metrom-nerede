# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request
from flask_cors import CORS

from gtfs_loader import get_store, get_store_optional
from live_metro import check_rate_limit, sefer_getir_iki_yon
from veriler_loader import get_metro_lines, get_stations_for_line
from tram_loader import get_tram_lines, get_stations_for_line as get_tram_stations_for_line

app = Flask(__name__)
CORS(app)


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/veriler/lines", methods=["GET"])
def veriler_lines():
    """metro-lines.json metro array'inden hat listesi: M1A, M1B, M2, ... (kaç tane varsa)."""
    lines = get_metro_lines()
    out = [{"code": L.get("code"), "name": L.get("name"), "lineId": L.get("lineId")} for L in lines]
    return jsonify(out)


@app.route("/api/veriler/lines/<code>/stations", methods=["GET"])
def veriler_line_stations(code):
    """Seçilen hattın durakları (örn. M1A → Atatürk Havalimanı, DTM-İstanbul Fuar Merkezi, ...)."""
    stations = get_stations_for_line(code)
    out = [{"stationId": s.get("stationId"), "name": s.get("name")} for s in stations]
    return jsonify(out)


@app.route("/api/veriler/lines/<code>/stations-with-arrivals", methods=["GET"])
def veriler_stations_with_arrivals(code):
    """
    Hattın tüm durakları; her biri için iki route (routes.name) ve ilk seferin dakikası.
    Metro İstanbul yanıtı: durum, sefer[] içinde zaman (HH:MM) -> dakikaya çevrilir.
    Rate limit nedeniyle çok durakta kısmi dönüş olabilir.
    """
    stations = get_stations_for_line(code)
    if not stations:
        return jsonify([])
    result = []
    client_ip = request.remote_addr or "127.0.0.1"
    for s in stations:
        station_id = s.get("stationId")
        name = (s.get("name") or "").strip()
        arrivals = []
        if check_rate_limit(client_ip):
            try:
                data = sefer_getir_iki_yon(code, name)
                for y in data.get("yonler", []):
                    arrivals.append({
                        "direction": y.get("yon") or "",
                        "minutes": y.get("minutes"),
                        "display": None,
                    })
            except Exception:
                pass
        result.append({
            "stationId": station_id,
            "name": name,
            "stop_id": str(station_id),
            "stop_name": name,
            "arrivals": arrivals,
        })
    return jsonify(result)


# ----- Tramvay (tram-lines.json) -----
@app.route("/api/tram/lines", methods=["GET"])
def tram_lines():
    """tram-lines.json tram array'inden hat listesi: T1, T3, T4, T5, ..."""
    lines = get_tram_lines()
    out = [{"code": L.get("code"), "name": L.get("name"), "lineId": L.get("lineId")} for L in lines]
    return jsonify(out)


@app.route("/api/tram/lines/<code>/stations", methods=["GET"])
def tram_line_stations(code):
    """Seçilen tramvay hattının durakları."""
    stations = get_tram_stations_for_line(code)
    out = [{"stationId": s.get("stationId"), "name": s.get("name")} for s in stations]
    return jsonify(out)


@app.route("/api/tram/lines/<code>/stations-with-arrivals", methods=["GET"])
def tram_stations_with_arrivals(code):
    """Hattın durakları; her biri için route'lar ve ilk seferin dakikası (canlı)."""
    stations = get_tram_stations_for_line(code)
    if not stations:
        return jsonify([])
    result = []
    client_ip = request.remote_addr or "127.0.0.1"
    for s in stations:
        station_id = s.get("stationId")
        name = (s.get("name") or "").strip()
        arrivals = []
        if check_rate_limit(client_ip):
            try:
                data = sefer_getir_iki_yon(code, name)
                for y in data.get("yonler", []):
                    arrivals.append({
                        "direction": y.get("yon") or "",
                        "minutes": y.get("minutes"),
                        "display": None,
                    })
            except Exception:
                pass
        result.append({
            "stationId": station_id,
            "name": name,
            "stop_id": str(station_id),
            "stop_name": name,
            "arrivals": arrivals,
        })
    return jsonify(result)


@app.route("/api/categories", methods=["GET"])
def categories():
    """Returns { metrolar: [...], tramvaylar: [...], marmaray: [...] }."""
    store = get_store_optional()
    if store:
        return jsonify(store.get_categories())
    # Vercel / GTFS yok: veriler + tram ile doldur (uygulama formatına uygun)
    metrolar = [{"route_id": L.get("code"), "route_short_name": L.get("code"), "route_long_name": L.get("name") or ""} for L in get_metro_lines()]
    tramvaylar = [{"route_id": L.get("code"), "route_short_name": L.get("code"), "route_long_name": L.get("name") or ""} for L in get_tram_lines()]
    return jsonify({"metrolar": metrolar, "tramvaylar": tramvaylar, "marmaray": []})


@app.route("/api/lines/<category>", methods=["GET"])
def lines(category):
    """Category: metrolar | tramvaylar | marmaray. Returns list of lines for that category."""
    store = get_store_optional()
    if store:
        cat = store.get_categories()
        key = category.lower()
        if key not in cat:
            return jsonify({"error": "Unknown category"}), 400
        return jsonify(cat[key])
    key = category.lower()
    if key == "metrolar":
        out = [{"route_id": L.get("code"), "route_short_name": L.get("code"), "route_long_name": L.get("name") or ""} for L in get_metro_lines()]
        return jsonify(out)
    if key == "tramvaylar":
        out = [{"route_id": L.get("code"), "route_short_name": L.get("code"), "route_long_name": L.get("name") or ""} for L in get_tram_lines()]
        return jsonify(out)
    if key == "marmaray":
        return jsonify([])
    return jsonify({"error": "Unknown category"}), 400


@app.route("/api/route/<route_id>/stations", methods=["GET"])
def route_stations(route_id):
    """Ordered list of stations for a route (line)."""
    store = get_store_optional()
    if store:
        stations = store.get_stations_for_route(route_id)
        return jsonify(stations)
    # GTFS yok: veriler/tram'dan durak listesi (route_id = hat kodu: M2, T1, ...)
    stations_metro = get_stations_for_line(route_id)
    if stations_metro:
        out = [{"stop_id": str(s.get("stationId")), "stop_name": s.get("name") or ""} for s in stations_metro]
        return jsonify(out)
    stations_tram = get_tram_stations_for_line(route_id)
    if stations_tram:
        out = [{"stop_id": str(s.get("stationId")), "stop_name": s.get("name") or ""} for s in stations_tram]
        return jsonify(out)
    return jsonify([])


@app.route("/api/route/<route_id>/station/<stop_id>/arrivals", methods=["GET"])
def station_arrivals(route_id, stop_id):
    """Next departures at this station for this route, by direction (e.g. Yıldız yönü -> 5 dk)."""
    store = get_store_optional()
    if store:
        arrivals = store.get_arrivals(route_id, stop_id)
        return jsonify(arrivals)
    # GTFS yok: canlı sefer dene (stop_id ile durak adı eşleşmesi gerekir; stop_name kullanılıyor)
    stop_name = request.args.get("stop_name") or stop_id
    if check_rate_limit(request.remote_addr or "127.0.0.1"):
        try:
            data = sefer_getir_iki_yon(route_id, stop_name)
            out = [{"direction": y.get("yon"), "minutes": y.get("minutes"), "display": None} for y in data.get("yonler", [])]
            return jsonify(out)
        except Exception:
            pass
    return jsonify([])


@app.route("/api/route/<route_id>/stations-with-arrivals", methods=["GET"])
def stations_with_arrivals(route_id):
    """
    All stations for the route, each with next arrivals per direction (GTFS/frekans).
    ?live=1 ile canlı veri dene (sadece desteklenen hatlar, rate limit var).
    """
    store = get_store_optional()
    use_live = request.args.get("live") == "1"

    if store:
        stations = store.get_stations_for_route(route_id)
        route_info = store.routes_by_id.get(route_id, {})
        hat = (route_info.get("route_short_name") or "").strip()
        result = []
        for s in stations:
            sid = s["stop_id"]
            stop_name = s["stop_name"]
            arrivals = []
            if use_live and hat and _try_live_arrivals(hat, stop_name, request, arrivals):
                pass
            else:
                for a in store.get_arrivals(route_id, sid):
                    arrivals.append({"direction": a.get("direction"), "minutes": a.get("minutes"), "display": a.get("display")})
            result.append({"stop_id": sid, "stop_name": stop_name, "arrivals": arrivals})
        return jsonify(result)

    # GTFS yok: veriler/tram durakları + (isteğe göre) canlı
    stations_metro = get_stations_for_line(route_id)
    stations_tram = get_tram_stations_for_line(route_id) if not stations_metro else []
    stations = stations_metro or stations_tram
    if not stations:
        return jsonify([])
    result = []
    client_ip = request.remote_addr or "127.0.0.1"
    for s in stations:
        sid = str(s.get("stationId"))
        stop_name = (s.get("name") or "").strip()
        arrivals = []
        if use_live and check_rate_limit(client_ip):
            _try_live_arrivals(route_id, stop_name, request, arrivals)
        result.append({"stop_id": sid, "stop_name": stop_name, "arrivals": arrivals})
    return jsonify(result)


def _try_live_arrivals(hat: str, stop_name: str, req, out: list) -> bool:
    if not check_rate_limit(req.remote_addr or "127.0.0.1"):
        return False
    try:
        data = sefer_getir_iki_yon(hat, stop_name, "Mahmutbey", "Yıldız (Mecidiyeköy)")
        for y in data.get("yonler", []):
            m = y.get("minutes")
            out.append({"direction": y.get("yon"), "minutes": m, "display": None})
        return bool(out)
    except Exception:
        return False


@app.route("/api/live/departures", methods=["GET"])
def live_departures():
    """
    Metro İstanbul canlı sefer (proxy). Rate limit: 30/dk/IP.
    Query: hat=M7, istasyon=Yenimahalle. İki yön (Mahmutbey + Yıldız) döner.
    """
    client_ip = request.remote_addr or "127.0.0.1"
    if not check_rate_limit(client_ip):
        return jsonify({"kaynak": "metro_istanbul", "yonler": [], "hata": "Çok fazla istek. Lütfen 1 dk bekleyin."}), 429
    hat = request.args.get("hat", "").strip()
    istasyon = request.args.get("istasyon", "").strip()
    if not hat or not istasyon:
        return jsonify({"error": "hat ve istasyon gerekli"}), 400
    try:
        data = sefer_getir_iki_yon(hat, istasyon, "Mahmutbey", "Yıldız (Mecidiyeköy)")
        return jsonify(data)
    except Exception as e:
        return jsonify({"kaynak": "metro_istanbul", "yonler": [], "hata": str(e)}), 500


if __name__ == "__main__":
    # Preload GTFS on startup (optional: csvs yoksa veriler/tram ile çalışır)
    get_store_optional()
    app.run(host="0.0.0.0", port=5000, debug=True)
