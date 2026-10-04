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
