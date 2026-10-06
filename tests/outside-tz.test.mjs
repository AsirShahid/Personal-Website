import test from "node:test";
import assert from "node:assert/strict";
import { formatOutsideTz } from "../src/utils/outside-tz.js";

test("short and minute-bearing offsets render in one canonical shape", () => {
  assert.equal(formatOutsideTz("UTC+2"), "UTC+02:00");
  assert.equal(formatOutsideTz("UTC+02:00"), "UTC+02:00");
  assert.equal(formatOutsideTz("UTC+5"), "UTC+05:00");
  assert.equal(formatOutsideTz("UTC+05:00"), "UTC+05:00");
  assert.equal(formatOutsideTz("UTC-4"), "UTC-04:00");
  assert.equal(formatOutsideTz("UTC-04:00"), "UTC-04:00");
  assert.equal(formatOutsideTz("UTC+12"), "UTC+12:00");
  assert.equal(formatOutsideTz("UTC+12:00"), "UTC+12:00");
});

test("half-hour and non-hour offsets keep their minutes", () => {
  assert.equal(formatOutsideTz("UTC+5:30"), "UTC+05:30");
  assert.equal(formatOutsideTz("UTC-3:30"), "UTC-03:30");
});

test("empty, missing and unknown values are preserved without inventing a zone", () => {
  assert.equal(formatOutsideTz(""), "");
  assert.equal(formatOutsideTz(undefined), "");
  assert.equal(formatOutsideTz(null), "");
  assert.equal(formatOutsideTz("  "), "");
  assert.equal(formatOutsideTz("Local time"), "Local time");
});

test("whitespace and case do not change the rendered zone", () => {
  assert.equal(formatOutsideTz(" utc+2 "), "UTC+02:00");
  assert.equal(formatOutsideTz("Utc-06:00"), "UTC-06:00");
});
