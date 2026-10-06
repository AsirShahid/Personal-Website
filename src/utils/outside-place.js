export function isOutsideTransitImage(image) {
  return image?.transit === true || image?.se === 0;
}

export function uniqueOutsidePlaces(images) {
  if (!Array.isArray(images)) return [];
  return Array.from(new Set(images.map((image) => image?.place?.trim()).filter((place) => Boolean(place))));
}

export function uniqueOutsideAreas(images) {
  if (!Array.isArray(images)) return [];
  return Array.from(new Set(images.map((image) => typeof image?.area === "string" ? image.area.trim() : "").filter(Boolean)));
}

function areasInStudyOrder(study, images) {
  const present = uniqueOutsideAreas(images);
  const configured = Array.isArray(study?.areaOrder)
    ? study.areaOrder.map((area) => typeof area === "string" ? area.trim() : "").filter(Boolean)
    : [];
  return [...configured.filter((area) => present.includes(area)), ...present.filter((area) => !configured.includes(area))];
}

/** Area-only worklist subtitle, ordered by the study's explicit areaOrder. */
export function getOutsideStudyAreaSummary(study) {
  const images = Array.isArray(study?.images) ? study.images : [];
  const ordered = areasInStudyOrder(study, images);
  const ordinaryAreas = new Set(uniqueOutsideAreas(images.filter((image) => !isOutsideTransitImage(image))));
  const transitAreas = new Set(uniqueOutsideAreas(images.filter(isOutsideTransitImage)));
  let ordinary = ordered.filter((area) => ordinaryAreas.has(area));
  const via = ordered.filter((area) => transitAreas.has(area));
  const studyPlace = typeof study?.place === "string" ? study.place.trim() : "";
  if (ordinary.length === 1 && ordinary[0] === studyPlace && study?.country) ordinary = [study.country];
  return [ordinary.join(" · "), via.length ? `via ${via.join(", ")}` : ""].filter(Boolean).join(" · ");
}

/** Return only explicit ordinary image areas for a date/area series strip cell. */
export function getOutsideSeriesArea(images) {
  return uniqueOutsideAreas(Array.isArray(images) ? images.filter((image) => !isOutsideTransitImage(image)) : []).join(" · ");
}

export function getOutsideStudyLocation(study) {
  const images = Array.isArray(study?.images) ? study.images : [];
  const places = uniqueOutsidePlaces(images.filter((image) => !isOutsideTransitImage(image)));
  const transitPlaces = uniqueOutsidePlaces(images.filter(isOutsideTransitImage));
  if (places.length === 1 && places[0] === study?.place && study?.country) places[0] = study.country;
  const primary = places.join(" · ");
  const via = transitPlaces.length ? `via ${transitPlaces.join(", ")}` : "";
  return [primary, via].filter(Boolean).join(" · ") || "Location unconfirmed";
}

export function getOutsideStudyCover(study) {
  const images = Array.isArray(study?.images) ? study.images : [];
  const preferred = images[study?.key];
  return (preferred && !isOutsideTransitImage(preferred) ? preferred : images.find((image) => !isOutsideTransitImage(image))) ?? null;
}

export function getOutsideFirstImageIndex(study) {
  const images = Array.isArray(study?.images) ? study.images : [];
  const firstSE1 = images.findIndex((image) => image?.se === 1);
  if (firstSE1 >= 0) return firstSE1;
  const firstOrdinary = images.findIndex((image) => !isOutsideTransitImage(image));
  return firstOrdinary >= 0 ? firstOrdinary : 0;
}
