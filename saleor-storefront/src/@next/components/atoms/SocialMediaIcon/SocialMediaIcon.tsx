import React from "react";

import { Icon } from "../Icon";

import * as S from "./styles";
import { IProps } from "./types";

export const SocialMediaIcon: React.FC<IProps> = ({
  medium,
  target,
}: IProps) => (
  <S.Wrapper>
    <S.Link
      href={medium.href}
      target={target || "_blank"}
      aria-label={medium.ariaLabel}
    >
      <Icon name={medium.iconName} size={36} />
    </S.Link>
  </S.Wrapper>
);
