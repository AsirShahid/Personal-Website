const outsideUtcZone = /^UTC([+-])(\d{1,2})(?::(\d{2}))?$/;

/**
 * Render one canonical UTC offset for the image overlay: sign, two-digit hours, two-digit minutes.
 * Source records spell the same offset several ways ("UTC+2", "UTC+02:00"), so the overlay must not
 * show two shapes for one zone. Unknown or empty values are preserved without inventing a zone.
 */
export function formatOutsideTz(value) {
  if (typeof value !== "string") return "";
  const trimmed = value.trim();
  const match = outsideUtcZone.exec(trimmed.toUpperCase());
  if (!match) return trimmed;
  const [, sign, hours, minutes] = match;
  return `UTC${sign}${hours.padStart(2, "0")}:${minutes ?? "00"}`;
}
