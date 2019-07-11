import * as React from "react";

import "./scss/index.scss";

type ButtonType = "submit" | "reset" | "button";
export interface ButtonProps extends React.HTMLProps<HTMLButtonElement> {
  secondary?: boolean;
  btnRef?: React.RefObject<HTMLButtonElement>;
}

const Button: React.FC<ButtonProps> = ({
  children,
  secondary,
  btnRef,
  type,
  ...otherProps
}) => (
  <button
    className={secondary ? "secondary" : ""}
    ref={btnRef}
    type={type as ButtonType}
    {...otherProps}
  >
    <span>{children}</span>
  </button>
);

export default Button;
