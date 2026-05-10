import type { SVGProps } from "react";

const Linux = (props: SVGProps<SVGSVGElement>) => (
  <svg {...props} viewBox="0 0 128 128">
    <rect width="128" height="128" rx="14" fill="#1a1a2e" />
    <path
      d="M22 40 L52 64 L22 88"
      stroke="#22c55e"
      strokeWidth="12"
      fill="none"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <rect x="62" y="80" width="44" height="12" rx="4" fill="#22c55e" />
  </svg>
);

export { Linux };
