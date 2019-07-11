import { icons } from "./definitions";

type IconName = keyof typeof icons;

export interface IProps {
  name: IconName;
  color?: string | string[];
  size?: number;
}
