import React from "react";

import { Icon } from "../Icon";

import * as S from "./styles";
import { IProps } from "./types";

export const IconButton: React.FC<IProps> = ({
  name,
  size = 36,
  onClick,
}: IProps) => {
  return (
    <S.Wrapper onClick={onClick}>
      <Icon name={name} size={size} />
    </S.Wrapper>
  );
};
