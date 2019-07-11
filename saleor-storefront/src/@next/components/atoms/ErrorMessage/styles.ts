import { styled } from "@styles";

export const ErrorMessage = styled.div`
  color: ${props => props.theme.colors.error};
  font-size: ${props => props.theme.input.labelFontSize};
`;

export const ErrorParagraph = styled.p`
  margin: 0;
`;

ErrorMessage.displayName = "S.ErrorMessage";
