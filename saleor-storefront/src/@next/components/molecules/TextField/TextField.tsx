import React from "react";

import * as S from "./styles";
import { IProps } from "./types";

import { ErrorMessage, Input } from "@components/atoms";

export const TextField: React.FC<IProps> = ({
  errors,
  helpText,
  ...rest
}: IProps) => {
  const hasErrors = !!(errors && errors.length);

  return (
    <S.TextField>
      <Input {...rest} error={hasErrors} />
      <ErrorMessage errors={errors} />
      {helpText && <S.HelpText>{helpText}</S.HelpText>}
    </S.TextField>
  );
};
