import type { SVGProps } from "react";

const Matlab = (props: SVGProps<SVGSVGElement>) => (
  <svg {...props} viewBox="0 0 128 128">
    <defs>
      <linearGradient id="matlab-wave" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stopColor="#0076A8" />
        <stop offset="50%" stopColor="#00AEEF" />
        <stop offset="100%" stopColor="#EF4135" />
      </linearGradient>
    </defs>
    <path
      d="M8 100 L32 44 Q44 20 56 50 Q68 80 80 30 Q92 -10 104 40 L120 100 Z"
      fill="url(#matlab-wave)"
    />
    <path
      d="M80 30 Q92 -10 104 40 L120 100 L100 100 Q90 60 80 30Z"
      fill="#EF4135"
      opacity="0.7"
    />
  </svg>
);

export { Matlab };
