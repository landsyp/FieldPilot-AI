from math import atan2, cos, radians, sin, sqrt
from typing import Protocol


class TrackPoint(Protocol):
    latitude: float
    longitude: float


EARTH_RADIUS_METERS = 6_371_000


def haversine_distance_meters(
    first_latitude: float,
    first_longitude: float,
    second_latitude: float,
    second_longitude: float,
) -> float:
    lat_delta = radians(second_latitude - first_latitude)
    lon_delta = radians(second_longitude - first_longitude)
    first_lat = radians(first_latitude)
    second_lat = radians(second_latitude)

    value = sin(lat_delta / 2) ** 2 + cos(first_lat) * cos(second_lat) * sin(lon_delta / 2) ** 2
    return EARTH_RADIUS_METERS * 2 * atan2(sqrt(value), sqrt(1 - value))


def total_distance_meters(points: list[TrackPoint]) -> float:
    if len(points) < 2:
        return 0

    distance = 0.0
    for previous_point, current_point in zip(points, points[1:]):
        distance += haversine_distance_meters(
            previous_point.latitude,
            previous_point.longitude,
            current_point.latitude,
            current_point.longitude,
        )
    return round(distance, 2)
