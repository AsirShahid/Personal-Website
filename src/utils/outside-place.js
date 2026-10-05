export function isOutsideTransitImage(image) {
  return image?.transit === true || image?.se === 0;
}

export function uniqueOutsidePlaces(images) {
  if (!Array.isArray(images)) return [];
  return Array.from(new Set(images.map((image) => image?.place?.trim()).filter((place) => Boolean(place))));
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
