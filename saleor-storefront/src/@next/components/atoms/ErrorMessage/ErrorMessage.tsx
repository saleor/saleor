import React from "react";

import * as S from "./styles";
import { IProps } from "./types";

export const ErrorMessage: React.FC<IProps> = ({ errors }: IProps) =>
  errors && errors.length ? (
    <S.ErrorMessage>
      {errors.map((error, index) => (
        <S.ErrorParagraph key={index}>{error.message}</S.ErrorParagraph>
      ))}
    </S.ErrorMessage>
  ) : null;
