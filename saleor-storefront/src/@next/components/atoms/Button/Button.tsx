import React from "react";

import * as S from "./styles";
import { IProps } from "./types";

export const Button: React.FC<IProps> = ({
  color = "primary",
  btnRef,
  children,
  ...props
}: IProps) => {
  const ButtonWithTheme = color === "primary" ? S.Primary : S.Secondary;

  return (
    <ButtonWithTheme color={color} ref={btnRef} {...props}>
      <S.Text>{children}</S.Text>
    </ButtonWithTheme>
  );
};
