import { media, styled } from "@styles";

export const Primary = styled.button<{ color: "primary" | "secondary" }>`
  background-color: ${props =>
    props.theme.button.colors[props.color].background};
  transform: skew(45deg);
  padding: 0.9rem 3.7rem;
  border: none;
  box-shadow: -5px 5px 14px 0px rgba(0, 0, 0, 0.2);
  transition: 0.3s;
  outline: none;
  font-family: ${props => props.theme.typography.baseFontFamily};
  cursor: pointer;
  color: ${props => props.theme.button.colors[props.color].color};

  &:hover {
    background-color: ${props =>
      props.theme.button.colors[props.color].hoverBackground};
    color: ${props => props.theme.button.colors[props.color].hoverColor};
  }

  &:active {
    background-color: ${props =>
      props.theme.button.colors[props.color].activeBackground};
    box-shadow: -3px 3px 14px 0px rgba(129, 67, 67, 0.2);
  }

  &:disabled {
    background-color: $gray;

    &,
    &:hover {
      cursor: default;
    }
  }

  ${media.smallScreen`
    padding:  0.9rem 1rem;
    width: 88%;
    max-width: 88%;
  `}
`;

export const Secondary = styled(Primary)`
  box-shadow: inset 0px 0px 0px 3px
    ${props => props.theme.button.colors.secondary.color};
  border-left: 1px solid ${props => props.theme.button.colors.secondary.color};
  border-right: 1px solid ${props => props.theme.button.colors.secondary.color};
`;

export const Text = styled.span`
  display: inline-block;
  font-size: 1.125rem;
  text-transform: uppercase;
  font-weight: ${props => props.theme.typography.boldFontWeight};
  line-height: ${props => props.theme.typography.baseLineHeight};
  transform: skew(-45deg);
`;
