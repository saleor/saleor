import React from "react";

import { icons } from "./definitions";
import { IProps } from "./types";

const getPathColor = (color: string | string[], index: number) => {
  if (typeof color === "string") {
    return color;
  }

  return color[index] ? color[index] : "inherit";
};

export const Icon: React.FC<IProps> = ({ size = 32, color, name }: IProps) => {
  const icon = icons[name];
  return (
    <svg height={size} viewBox="0 0 32 32" width={size}>
      {icon &&
        icon.map((path, index) => (
          <path
            d={path.d}
            fill={color ? getPathColor(color, index) : path.fill}
            key={index}
          />
        ))}
    </svg>
  );
};

export { IProps as IIcon };
