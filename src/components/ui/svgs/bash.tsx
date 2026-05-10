import type { SVGProps } from "react";

const Bash = (props: SVGProps<SVGSVGElement>) => (
  <svg {...props} viewBox="0 0 128 128">
    <rect width="128" height="128" rx="14" fill="#1d2021" />
    <rect x="16" y="30" width="96" height="8" rx="4" fill="#4a4a4a" />
    <path
      d="M16 54 L38 64 L16 74"
      stroke="#4EAA25"
      strokeWidth="8"
      fill="none"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <rect x="46" y="60" width="30" height="8" rx="3" fill="#4EAA25" />
    <rect x="16" y="88" width="60" height="8" rx="3" fill="#4a4a4a" />
    <rect x="16" y="106" width="40" height="8" rx="3" fill="#4a4a4a" />
  </svg>
);

export { Bash };
