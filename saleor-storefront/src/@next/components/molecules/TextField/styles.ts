import { styled } from "@styles";

export const TextField = styled.div`
  margin-bottom: ${props => props.theme.spacing.spacer};
`;
TextField.displayName = "S.TextField";

export const HelpText = styled.span`
  color: ${props => props.theme.input.labelColor};
  font-size: ${props => props.theme.input.labelFontSize};
`;
