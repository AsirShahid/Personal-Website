import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { getOutsideSeriesArea, getOutsideStudyAreaSummary } from "../src/utils/outside-place.js";

const area = (name, transit = false, place = name) => ({ area: name, place, transit });

test("worklist area summary follows explicit areaOrder and separates via areas", () => {
  const study = {
    place: "Australia",
    areaOrder: ["South West", "Rottnest Island", "Perth"],
    images: [area("Bangkok", true), area("Perth"), area("South West"), area("South West"), area("Rottnest Island")],
  };
  assert.equal(getOutsideStudyAreaSummary(study), "South West · Rottnest Island · Perth · via Bangkok");
});

test("Pakistan areas use requested worklist order before Rome and Tirana transit", () => {
  assert.equal(getOutsideStudyAreaSummary({
    place: "Pakistan",
    areaOrder: ["Karachi", "Islamabad", "Murree", "Lahore"],
    images: [area("Rome", true), area("Tirana", true), area("Lahore"), area("Murree"), area("Islamabad"), area("Karachi")],
  }), "Karachi · Islamabad · Murree · Lahore · via Rome, Tirana");
});

test("worklist area summary omits absent ordered areas and keeps Montreal's country subtitle", () => {
  assert.equal(getOutsideStudyAreaSummary({
    place: "Montréal",
    country: "Canada",
    areaOrder: ["Montréal", "Québec City"],
    images: [area("Montréal", false, "Old Montréal")],
  }), "Canada");
});

test("area labels never fall back to image.place or study.place", () => {
  assert.equal(getOutsideStudyAreaSummary({ place: "Tirana", images: [{ place: "Tirana", transit: true }] }), "");
  assert.equal(getOutsideStudyAreaSummary({ place: "Karachi", images: [area("Karachi", true)] }), "via Karachi");
});

test("series location uses image areas, not detailed image places", () => {
  assert.equal(getOutsideSeriesArea([area("South West", false, "Hamelin Bay"), area("South West", false, "Augusta")] ), "South West");
  assert.equal(getOutsideSeriesArea([area("Bangkok", true)]), "");
});

test("worklist keeps the two-line clamp safety and series cells are fixed thumb-width", () => {
  const source = readFileSync(new URL("../src/pages/outside.astro", import.meta.url), "utf8");
  assert.match(source, /\.oz-region\s*\{[^}]*-webkit-line-clamp:\s*2/s);
  assert.match(source, /\.oz-se\s*\{[^}]*flex:\s*0 0 104px;[^}]*width:\s*104px;[^}]*min-width:\s*0/s);
  assert.match(source, /\.oz-se-cap\s*\{[^}]*width:\s*100%;[^}]*min-width:\s*0/s);
  assert.match(source, /\.oz-series\s*\{[^}]*gap:\s*8px/s);
  assert.match(source, /\.oz-se img\s*\{[^}]*width:\s*104px/s);
  assert.match(source, /@media \(max-width: 899px\)[\s\S]*?\.oz-se img\s*\{[^}]*width:\s*84px/s);
  assert.match(source, /const imagePlace = \[img\.place\?\.trim\(\), isOutsideTransitImage\(img\) \? "TRANSIT" : ""\]/);
  assert.match(source, /name\.textContent = seriesHeading;[\s\S]*?detail\.textContent = chapterName;/);
});
