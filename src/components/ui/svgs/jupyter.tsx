import type { SVGProps } from "react";

const Jupyter = (props: SVGProps<SVGSVGElement>) => (
  <svg {...props} viewBox="0 0 128 128">
    <circle cx="64" cy="64" r="60" fill="white" />
    <path
      fill="#F37726"
      d="M64 8C33.1 8 8 33.1 8 64s25.1 56 56 56 56-25.1 56-56S94.9 8 64 8zm0 8c26.5 0 48 21.5 48 48S90.5 112 64 112 16 90.5 16 64s21.5-48 48-48z"
    />
    <circle cx="64" cy="16" r="8" fill="#767677" />
    <circle cx="22" cy="100" r="8" fill="#F37726" />
    <circle cx="106" cy="100" r="8" fill="#9E9E9E" />
    <ellipse cx="64" cy="64" rx="30" ry="18" fill="none" stroke="#F37726" strokeWidth="6" />
    <ellipse cx="64" cy="64" rx="30" ry="18" fill="none" stroke="#F37726" strokeWidth="6" transform="rotate(60 64 64)" />
    <ellipse cx="64" cy="64" rx="30" ry="18" fill="none" stroke="#F37726" strokeWidth="6" transform="rotate(120 64 64)" />
    <circle cx="64" cy="64" r="8" fill="#F37726" />
  </svg>
);

export { Jupyter };
