import test from "node:test";
import assert from "node:assert/strict";
import { formatOutsideDateRange } from "../src/utils/outside-date.js";

test("date ranges show both years when they cross a calendar year", () => {
  assert.equal(formatOutsideDateRange("2023-05-14", "2025-06-18"), "2023-05-14 to 2025-06-18");
});

test("same-year ranges may shorten only the end year", () => {
  assert.equal(formatOutsideDateRange("2025-06-14", "2025-06-18"), "2025-06-14 to 06-18");
});

test("unknown and partial dates are preserved without invented values", () => {
  assert.equal(formatOutsideDateRange("", ""), "");
  assert.equal(formatOutsideDateRange("2023-05", ""), "2023-05");
  assert.equal(formatOutsideDateRange("2023-05", "2025-06-18"), "2023-05 to 2025-06-18");
});

test("invalid or reversed full dates are not shortened as valid ranges", () => {
  assert.equal(formatOutsideDateRange("2025-13-01", "2025-13-02"), "2025-13-01 to 2025-13-02");
  assert.equal(formatOutsideDateRange("2025-06-18", "2025-06-14"), "2025-06-18 to 2025-06-14");
});
