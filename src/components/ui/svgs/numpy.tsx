import type { SVGProps } from "react";

const NumPy = (props: SVGProps<SVGSVGElement>) => (
  <svg {...props} viewBox="0 0 128 128">
    <path fill="#4DABCF" d="M60 8L8 36v28l52-28 52 28V36z" />
    <path fill="#4DABCF" d="M8 64v28l52 28 52-28V64L60 92z" opacity="0.7" />
    <path fill="#013243" d="M60 8L8 36l52 28 52-28z" opacity="0.15" />
    <path fill="#4DABCF" d="M60 36L34 50v24l26 14 26-14V50z" />
    <path fill="#013243" d="M60 36L34 50l26 14 26-14z" opacity="0.2" />
    <path fill="white" d="M60 50l-14 8v14l14 8 14-8V58z" opacity="0.9" />
  </svg>
);

export { NumPy };
