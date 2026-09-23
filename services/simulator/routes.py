import json
import math
import pathlib

ROUTES_FILE = pathlib.Path(__file__).parent / "db" / "seed" / "routes.json"


def load_routes() -> dict:
    return json.loads(ROUTES_FILE.read_text())


def _haversine_km(a, b):
    lat1, lon1 = a
    lat2, lon2 = b
    r = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    x = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(x))


def _bearing(a, b):
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


class RoutePlayer:
    """Walks a truck back and forth along a polyline at a roughly constant speed."""

    def __init__(self, waypoints: list[list[float]], speed_kmh: float = 62.0, offset: float = 0.0):
        self.waypoints = [tuple(w) for w in waypoints]
        self.speed_kmh = speed_kmh
        self.leg_km = [
            _haversine_km(self.waypoints[i], self.waypoints[i + 1])
            for i in range(len(self.waypoints) - 1)
        ]
        self.total_km = sum(self.leg_km)
        self.distance = offset * self.total_km
        self.direction = 1

    def advance(self, seconds: float):
        km = self.speed_kmh * (seconds / 3600.0)
        self.distance += km * self.direction
        if self.distance >= self.total_km:
            self.distance = self.total_km
            self.direction = -1
        elif self.distance <= 0:
            self.distance = 0
            self.direction = 1

    def position(self):
        remaining = self.distance
        for i, leg in enumerate(self.leg_km):
            if remaining <= leg or i == len(self.leg_km) - 1:
                frac = 0 if leg == 0 else min(remaining / leg, 1.0)
                a, b = self.waypoints[i], self.waypoints[i + 1]
                lat = a[0] + (b[0] - a[0]) * frac
                lon = a[1] + (b[1] - a[1]) * frac
                heading = _bearing(a, b) if self.direction > 0 else _bearing(b, a)
                return lat, lon, heading
            remaining -= leg
        a, b = self.waypoints[-2], self.waypoints[-1]
        return self.waypoints[-1][0], self.waypoints[-1][1], _bearing(a, b)
