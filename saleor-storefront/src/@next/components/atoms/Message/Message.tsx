import React from "react";

import { Icon } from "../Icon";
import * as S from "./styles";
import { IProps } from "./types";

export const Message: React.FC<IProps> = ({
  title,
  status = "neutral",
  children,
  onClick,
  actionText,
}: IProps) => {
  const isAction = status === "action";

  return (
    <S.Wrapper status={status}>
      <S.TopWrapper>
        <S.Title>{title}</S.Title>
        {isAction ? (
          !children && (
            <S.ActionButton onClick={onClick}>{actionText}</S.ActionButton>
          )
        ) : (
          <S.CloseButton onClick={onClick}>
            <Icon name="x" size={15} />
          </S.CloseButton>
        )}
      </S.TopWrapper>
      {children && <S.Content>{children}</S.Content>}
      {children && isAction && (
        <S.ActionButton onClick={onClick} style={{ marginTop: "1rem" }}>
          {actionText}
        </S.ActionButton>
      )}
    </S.Wrapper>
  );
};
