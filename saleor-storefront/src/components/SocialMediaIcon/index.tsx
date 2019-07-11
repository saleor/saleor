import * as React from "react";
import ReactSVG from "react-svg";
import "./scss/index.scss";

interface Medium {
  ariaLabel: string;
  path: string;
  href: string;
}

export interface IconProps extends React.HTMLProps<HTMLAnchorElement> {
  medium: Medium;
  target?: string;
}

const SocialMediaIcon: React.FC<IconProps> = ({ medium, target }) => (
  <a
    href={medium.href}
    target={target || "_blank"}
    aria-label={medium.ariaLabel}
  >
    <ReactSVG path={medium.path} className="social-icon" />
  </a>
);

export default SocialMediaIcon;
