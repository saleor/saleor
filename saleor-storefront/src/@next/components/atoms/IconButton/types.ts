import { IIcon } from "../Icon";

export interface IProps extends IIcon {
  onClick?: () => void;
}
