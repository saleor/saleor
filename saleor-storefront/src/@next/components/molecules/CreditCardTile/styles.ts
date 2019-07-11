import { styled } from "@styles";

export const BoldTitle = styled.div`
  font-weight: ${props => props.theme.typography.boldFontWeight};
`;

export const TextContent = styled.div`
  margin-top: 0.5rem;
  margin-bottom: ${props => props.theme.spacing.spacer};
`;

export const FooterContent = styled.div`
  > div {
    display: inline-block;
    padding: 0;
    margin: 0;
    margin-right: 0.6rem;
  }
`;
