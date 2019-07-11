import React from "react";

import { GlobalStyle } from "../src/@next/globalStyles";
import * as S from "./styles";

export const OutLineDecorator = storyFn => (
  <S.Wrapper>
    {storyFn()}
    <S.Outline />
    <GlobalStyle />
  </S.Wrapper>
);
