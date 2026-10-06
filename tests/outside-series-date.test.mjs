import test from "node:test";
import assert from "node:assert/strict";
import { formatOutsideSeriesDate } from "../src/utils/outside-date.js";

test("series strip dates omit the year without inventing a date", () => {
  assert.equal(formatOutsideSeriesDate("2026-07-11"), "Jul 11");
  assert.equal(formatOutsideSeriesDate("2026-07-11T10:00:00Z"), "2026-07-11T10:00:00Z");
  assert.equal(formatOutsideSeriesDate(""), "");
  assert.equal(formatOutsideSeriesDate(null), "");
});
