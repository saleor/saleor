import { styled } from "@styles";
import { css } from "styled-components";

interface WrapperProps {
  readonly hover?: boolean;
}

export const Wrapper = styled.div<WrapperProps>`
  background-color: ${props => props.theme.tile.backgroundColor};
  border: 1px transparent solid;
  padding: 0;
  ${props =>
    props.hover &&
    css`
      :hover {
        cursor: pointer;
        border-color: ${props.theme.tile.hoverBorder};
      }
    `}
`;

export const Header = styled.div`
  border-bottom: 2px solid ${props => props.theme.tile.divisionLine};
`;

export const Content = styled.div`
  padding: 1rem 1.25rem;
`;

export const Footer = styled.div`
  padding: 0 1rem;
  margin-bottom: 1rem;
`;
