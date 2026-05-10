import type { SVGProps } from "react";

const Pandas = (props: SVGProps<SVGSVGElement>) => (
  <svg {...props} viewBox="0 0 128 128">
    <rect x="50" y="8" width="28" height="52" rx="14" fill="#130754" />
    <rect x="50" y="68" width="28" height="52" rx="14" fill="#130754" />
    <rect x="8" y="36" width="28" height="56" rx="14" fill="#e70488" />
    <rect x="92" y="36" width="28" height="56" rx="14" fill="#e70488" />
    <rect x="38" y="44" width="52" height="40" rx="8" fill="#130754" />
    <rect x="44" y="52" width="16" height="16" rx="4" fill="white" />
    <rect x="68" y="52" width="16" height="16" rx="4" fill="white" />
    <rect x="50" y="72" width="28" height="6" rx="3" fill="#e70488" />
  </svg>
);

export { Pandas };
