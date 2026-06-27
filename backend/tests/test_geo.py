from app.services.geo import haversine_distance_meters, total_distance_meters


class Point:
    def __init__(self, latitude: float, longitude: float) -> None:
        self.latitude = latitude
        self.longitude = longitude


def test_haversine_distance_meters() -> None:
    distance = haversine_distance_meters(45.5019, -73.5674, 45.5029, -73.5674)

    assert 110 < distance < 112


def test_total_distance_meters() -> None:
    distance = total_distance_meters(
        [
            Point(45.5019, -73.5674),
            Point(45.5024, -73.5674),
            Point(45.5029, -73.5674),
        ]
    )

    assert 110 < distance < 112
