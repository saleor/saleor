import React from "react";

import * as S from "./styles";
import { IProps } from "./types";

export const Input: React.FC<IProps> = ({
  onBlur,
  onFocus,
  contentLeft = null,
  contentRight = null,
  error = false,
  disabled = false,
  placeholder,
  label,
  value,
  onChange,
  ...props
}: IProps) => {
  const [active, setActive] = React.useState(false);

  const handleFocus = React.useCallback(
    e => {
      setActive(true);
      if (onFocus) {
        onFocus(e);
      }
    },
    [setActive, onFocus]
  );
  const handleBlur = React.useCallback(
    e => {
      setActive(false);
      if (onBlur) {
        onBlur(e);
      }
    },
    [setActive, onBlur]
  );

  return (
    <S.Wrapper active={active} error={error} disabled={disabled}>
      {contentLeft && <S.Content>{contentLeft}</S.Content>}
      <S.InputWrapper>
        <S.Input
          {...props}
          value={value}
          onFocus={handleFocus}
          onBlur={handleBlur}
          disabled={disabled}
          onChange={onChange}
        />
        {label && <S.Label active={active || !!value}>{label}</S.Label>}
      </S.InputWrapper>
      {contentRight && <S.Content>{contentRight}</S.Content>}
    </S.Wrapper>
  );
};
