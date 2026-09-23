import json
import math
import pathlib

ROUTES_FILE = pathlib.Path(__file__).parent / "db" / "seed" / "routes.json"
_label_to_destination: dict[str, tuple[float, float]] | None = None


def _load_destinations() -> dict[str, tuple[float, float]]:
    global _label_to_destination
    if _label_to_destination is None:
        routes = json.loads(ROUTES_FILE.read_text())
        _label_to_destination = {r["label"]: tuple(r["waypoints"][-1]) for r in routes.values()}
    return _label_to_destination


def _haversine_km(a, b):
    lat1, lon1 = a
    lat2, lon2 = b
    r = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    x = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(x))


def eta_minutes(route_name: str, lat: float, lon: float, speed_kmh: float) -> float | None:
    dest = _load_destinations().get(route_name)
    if not dest or speed_kmh <= 0:
        return None
    remaining_km = _haversine_km((lat, lon), dest)
    return round((remaining_km / speed_kmh) * 60, 1)
