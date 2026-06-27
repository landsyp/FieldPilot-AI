import type { GpsPoint } from "@/lib/types";

const EARTH_RADIUS_METERS = 6_371_000;

export function haversineDistanceMeters(
  firstLatitude: number,
  firstLongitude: number,
  secondLatitude: number,
  secondLongitude: number,
) {
  const latDelta = toRadians(secondLatitude - firstLatitude);
  const lonDelta = toRadians(secondLongitude - firstLongitude);
  const firstLat = toRadians(firstLatitude);
  const secondLat = toRadians(secondLatitude);

  const value =
    Math.sin(latDelta / 2) ** 2 +
    Math.cos(firstLat) * Math.cos(secondLat) * Math.sin(lonDelta / 2) ** 2;

  return EARTH_RADIUS_METERS * 2 * Math.atan2(Math.sqrt(value), Math.sqrt(1 - value));
}

export function calculateDistanceMeters(points: Pick<GpsPoint, "latitude" | "longitude">[]) {
  if (points.length < 2) {
    return 0;
  }

  return Number(
    points
      .slice(1)
      .reduce((distance, point, index) => {
        const previousPoint = points[index];
        return (
          distance +
          haversineDistanceMeters(
            previousPoint.latitude,
            previousPoint.longitude,
            point.latitude,
            point.longitude,
          )
        );
      }, 0)
      .toFixed(2),
  );
}

export function formatDuration(totalSeconds: number) {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

function toRadians(value: number) {
  return (value * Math.PI) / 180;
}
