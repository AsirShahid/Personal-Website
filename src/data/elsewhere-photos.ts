export interface ElsewherePhoto {
  id: string;
  src: string;
  pixelWidth: number;
  pixelHeight: number;
  place: string;
  routeLabel: string;
  note: string;
  alt: string;
  credit: string;
  license: string;
  licenseUrl: string;
  source: string;
  sourceTitle: string;
  desktopWidth: number;
  desktopHeight: number;
  mobileHeight: number;
  lift: number;
}

// Replace this one manifest and its matching local files when Asir's own
// photographs are ready. Until then every image is explicitly identified as a
// sample and its source, photographer, and reuse license stay attached here.
export const ELSEWHERE_PHOTOS: ElsewherePhoto[] = [
  {
    id: "dakhla",
    src: "/images/elsewhere/dakhla.webp",
    pixelWidth: 1600,
    pixelHeight: 1067,
    place: "Dakhla Oasis, Egypt",
    routeLabel: "Dakhla",
    note: "Wind-shaped sand and shadow",
    alt: "Fine sand ripples catch warm light in Dakhla Oasis, Egypt.",
    credit: "Vyacheslav Argenberg",
    license: "CC BY 4.0",
    licenseUrl: "https://creativecommons.org/licenses/by/4.0/",
    source: "https://commons.wikimedia.org/wiki/File:Sand_dunes_in_the_desert,_Sahara_Desert,_Dakhla_Oasis,_Egypt.jpg",
    sourceTitle: "Sand dunes in the desert, Sahara Desert, Dakhla Oasis, Egypt",
    desktopWidth: 26,
    desktopHeight: 16.8,
    mobileHeight: 54,
    lift: 20,
  },
  {
    id: "half-moon-bay",
    src: "/images/elsewhere/half-moon-bay.webp",
    pixelWidth: 1600,
    pixelHeight: 1201,
    place: "Half Moon Bay, California",
    routeLabel: "Half Moon Bay",
    note: "Wildflowers above the Pacific",
    alt: "Red flowers and ocean cliffs above a curving beach in Half Moon Bay, California.",
    credit: "Elena.laps",
    license: "CC BY-SA 4.0",
    licenseUrl: "https://creativecommons.org/licenses/by-sa/4.0/",
    source: "https://commons.wikimedia.org/wiki/File:View_of_the_coastal_cliffs_in_Half_Moon_Bay,_California.jpg",
    sourceTitle: "View of the coastal cliffs in Half Moon Bay, California",
    desktopWidth: 23,
    desktopHeight: 18.1,
    mobileHeight: 58,
    lift: 2,
  },
  {
    id: "arashiyama",
    src: "/images/elsewhere/arashiyama.webp",
    pixelWidth: 1600,
    pixelHeight: 1067,
    place: "Arashiyama, Kyoto",
    routeLabel: "Arashiyama",
    note: "A green corridor through the city",
    alt: "Tall bamboo trunks fill the grove at Arashiyama in Kyoto, Japan.",
    credit: "Basile Morin",
    license: "CC BY-SA 4.0",
    licenseUrl: "https://creativecommons.org/licenses/by-sa/4.0/",
    source: "https://commons.wikimedia.org/wiki/File:Bamboo_Forest,_Arashiyama,_Kyoto,_Japan.jpg",
    sourceTitle: "Bamboo Forest, Arashiyama, Kyoto, Japan",
    desktopWidth: 22,
    desktopHeight: 17.6,
    mobileHeight: 56,
    lift: 24,
  },
  {
    id: "chola-valley",
    src: "/images/elsewhere/chola-valley.webp",
    pixelWidth: 1600,
    pixelHeight: 1067,
    place: "Chola Valley, Nepal",
    routeLabel: "Chola Valley",
    note: "A lake beneath clouded peaks",
    alt: "A turquoise glacial lake beneath mist-covered mountains in Chola Valley, Nepal.",
    credit: "Vyacheslav Argenberg",
    license: "CC BY 4.0",
    licenseUrl: "https://creativecommons.org/licenses/by/4.0/",
    source: "https://commons.wikimedia.org/wiki/File:Chola_Mountain_Lake,_Nepal.jpg",
    sourceTitle: "Chola Mountain Lake, Nepal",
    desktopWidth: 27,
    desktopHeight: 17.8,
    mobileHeight: 60,
    lift: 12,
  },
  {
    id: "dolomites",
    src: "/images/elsewhere/dolomites.webp",
    pixelWidth: 1600,
    pixelHeight: 1065,
    place: "Dolomites, Italy",
    routeLabel: "Dolomites",
    note: "The ridgeline keeps its weather",
    alt: "Jagged Dolomite peaks rise through drifting clouds above a green alpine slope.",
    credit: "Dmitry Djouce",
    license: "CC BY 4.0",
    licenseUrl: "https://creativecommons.org/licenses/by/4.0/",
    source: "https://commons.wikimedia.org/wiki/File:Near_Forcella_Venegiotta_-_Dolomites,_Italy.jpg",
    sourceTitle: "Near Forcella Venegiotta, Dolomites, Italy",
    desktopWidth: 24,
    desktopHeight: 17.4,
    mobileHeight: 58,
    lift: 22,
  },
  {
    id: "venice",
    src: "/images/elsewhere/venice.webp",
    pixelWidth: 1600,
    pixelHeight: 1116,
    place: "Venice, Italy",
    routeLabel: "Venice",
    note: "The Grand Canal after sunset",
    alt: "Santa Maria della Salute and gondolas beside the Grand Canal in Venice at dusk.",
    credit: "Stavros Argyropoulos",
    license: "CC BY-SA 4.0",
    licenseUrl: "https://creativecommons.org/licenses/by-sa/4.0/",
    source: "https://commons.wikimedia.org/wiki/File:Venice_-_Flickr_-_Stavrarg.jpg",
    sourceTitle: "Venice, Grand Canal and Santa Maria della Salute",
    desktopWidth: 28,
    desktopHeight: 18.1,
    mobileHeight: 60,
    lift: 5,
  },
];
