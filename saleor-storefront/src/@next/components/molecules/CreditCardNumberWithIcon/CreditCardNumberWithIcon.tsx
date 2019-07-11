import React from "react";

import { CreditCardIcon } from "@components/atoms";

import * as S from "./styles";
import { IProps } from "./types";

export const CreditCardNumberWithIcon: React.FC<IProps> = ({
  provider,
  last4Digits,
}) => {
  return (
    <div>
      <CreditCardIcon provider={provider} />
      <S.Wrapper>XXXX XXXX XXXX {last4Digits}</S.Wrapper>
    </div>
  );
};
