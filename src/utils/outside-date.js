const completeIsoDate = /^\d{4}-\d{2}-\d{2}$/;

function isValidIsoDate(value) {
  if (!completeIsoDate.test(value)) return false;
  const [year, month, day] = value.split("-").map(Number);
  const parsed = new Date(Date.UTC(year, month - 1, day));
  return parsed.getUTCFullYear() === year && parsed.getUTCMonth() === month - 1 && parsed.getUTCDate() === day;
}

/** Render dates without hiding cross-year boundaries or filling unknown/invalid fields. */
export function formatOutsideDateRange(start, end) {
  if (typeof start !== "string") start = "";
  if (typeof end !== "string") end = "";
  if (!start) return end;
  if (!end || start === end) return start;

  const bothValid = isValidIsoDate(start) && isValidIsoDate(end);
  if (!bothValid || start.slice(0, 4) !== end.slice(0, 4) || end < start) return `${start} to ${end}`;
  return `${start} to ${end.slice(5)}`;
}

const monthAbbreviations = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** Compact row/strip dates while retaining month and year boundaries. */
export function formatOutsideCompactDateRange(start, end) {
  if (typeof start !== "string") start = "";
  if (typeof end !== "string") end = "";
  if (!start) return end;

  const parts = (value) => {
    if (!isValidIsoDate(value)) return null;
    const [year, month, day] = value.split("-").map(Number);
    return { year, month, day };
  };
  const first = parts(start);
  const last = parts(end || start);
  const dateText = ({ month, day }) => `${monthAbbreviations[month - 1]} ${day}`;

  if (!first || !last || (end && end < start)) return end && start !== end ? `${start} to ${end}` : start;
  if (!end || start === end) return `${dateText(first)}, ${first.year}`;
  if (first.year === last.year && first.month === last.month) {
    return `${monthAbbreviations[first.month - 1]} ${first.day}–${last.day}, ${first.year}`;
  }
  if (first.year === last.year) return `${dateText(first)} – ${dateText(last)}, ${first.year}`;
  return `${dateText(first)}, ${first.year} – ${dateText(last)}, ${last.year}`;
}

/** Format one series day as a compact month/day label without a year. */
export function formatOutsideSeriesDate(value) {
  if (typeof value !== "string" || !value) return "";
  if (!isValidIsoDate(value)) return value;
  const [, month, day] = value.split("-").map(Number);
  return `${monthAbbreviations[month - 1]} ${day}`;
}
