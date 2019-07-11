import React from "react";

export interface IProps extends React.HTMLAttributes<HTMLButtonElement> {
  color?: "primary" | "secondary";
  btnRef?: React.RefObject<HTMLButtonElement>;
}
