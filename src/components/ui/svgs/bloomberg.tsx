import type { SVGProps } from "react";

const Bloomberg = (props: SVGProps<SVGSVGElement>) => (
  <svg {...props} viewBox="0 0 128 128">
    <rect width="128" height="128" fill="#000000" />
    <path
      fill="#F26522"
      d="M24 24h32c13 0 22 7 22 19 0 7-4 13-10 16 8 3 13 10 13 19 0 14-10 22-25 22H24V24zm14 30h16c6 0 10-3 10-9s-4-9-10-9H38v18zm0 32h18c7 0 11-4 11-10s-4-10-11-10H38v20z"
    />
  </svg>
);

export { Bloomberg };
