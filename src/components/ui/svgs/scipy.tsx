import type { SVGProps } from "react";

const SciPy = (props: SVGProps<SVGSVGElement>) => (
  <svg {...props} viewBox="0 0 128 128">
    <circle cx="64" cy="64" r="60" fill="#0C55A5" />
    <path
      fill="white"
      d="M64 24C42 24 28 38 28 52c0 10 7 18 18 22-4 2-8 6-8 12 0 10 12 18 26 18s26-8 26-18c0-6-4-10-8-12 11-4 18-12 18-22 0-14-14-28-36-28zm0 12c10 0 18 6 18 14s-8 14-18 14-18-6-18-14 8-14 18-14zm0 52c-8 0-14-4-14-8s6-8 14-8 14 4 14 8-6 8-14 8z"
    />
  </svg>
);

export { SciPy };
