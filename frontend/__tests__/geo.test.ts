import { describe, expect, it } from "vitest";

import { calculateDistanceMeters, formatDuration, haversineDistanceMeters } from "@/lib/geo";

describe("geo utilities", () => {
  it("calculates haversine distance in meters", () => {
    const distance = haversineDistanceMeters(45.5019, -73.5674, 45.5029, -73.5674);

    expect(distance).toBeGreaterThan(110);
    expect(distance).toBeLessThan(112);
  });

  it("sums a GPS path", () => {
    const distance = calculateDistanceMeters([
      { latitude: 45.5019, longitude: -73.5674 },
      { latitude: 45.5024, longitude: -73.5674 },
      { latitude: 45.5029, longitude: -73.5674 },
    ]);

    expect(distance).toBeGreaterThan(110);
    expect(distance).toBeLessThan(112);
  });

  it("formats treatment duration", () => {
    expect(formatDuration(65)).toBe("1:05");
  });
});
