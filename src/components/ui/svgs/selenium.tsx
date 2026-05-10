import type { SVGProps } from "react";

const Selenium = (props: SVGProps<SVGSVGElement>) => (
  <svg {...props} viewBox="0 0 128 128">
    <circle cx="64" cy="64" r="58" fill="#43B02A" />
    <path
      d="M36 52 Q64 28 92 52 Q64 76 36 52Z"
      fill="white"
      opacity="0.9"
    />
    <path
      d="M36 76 Q64 52 92 76 Q64 100 36 76Z"
      fill="white"
      opacity="0.6"
    />
    <circle cx="64" cy="64" r="10" fill="white" />
  </svg>
);

export { Selenium };
