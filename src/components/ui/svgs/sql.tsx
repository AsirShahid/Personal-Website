import type { SVGProps } from "react";

const SQL = (props: SVGProps<SVGSVGElement>) => (
  <svg {...props} viewBox="0 0 128 128">
    <ellipse cx="64" cy="32" rx="44" ry="16" fill="#00758F" />
    <path fill="#00758F" d="M20 32v20c0 8.8 19.6 16 44 16s44-7.2 44-16V32c0 8.8-19.6 16-44 16S20 40.8 20 32z" />
    <path fill="#00758F" d="M20 52v20c0 8.8 19.6 16 44 16s44-7.2 44-16V52c0 8.8-19.6 16-44 16S20 60.8 20 52z" opacity="0.85" />
    <path fill="#00758F" d="M20 72v20c0 8.8 19.6 16 44 16s44-7.2 44-16V72c0 8.8-19.6 16-44 16S20 80.8 20 72z" opacity="0.7" />
    <ellipse cx="64" cy="32" rx="44" ry="16" fill="none" stroke="#005E73" strokeWidth="2" />
  </svg>
);

export { SQL };
