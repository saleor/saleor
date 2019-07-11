import { createGlobalStyle } from "styled-components";
import { DefaultTheme } from ".";

export const GlobalStyle = createGlobalStyle<{ theme: DefaultTheme }>`
  html {
    box-sizing: border-box;
  }

  *, *:before, *:after {
    box-sizing: inherit;
  }

  body {
    min-width: 320px;
    font-family: ${props => props.theme.typography.baseFontFamily};
    font-size: ${props => props.theme.typography.baseFontSize};
    line-height: ${props => props.theme.typography.baseLineHeight};
    color: ${props => props.theme.colors.baseFont};
  }

  h1 {
    font-size: ${props => props.theme.typography.h1FontSize};
    line-height: ${props => props.theme.typography.h1LineHeight};
  }

  h3 {
    font-size: ${props => props.theme.typography.h3FontSize};
    line-height: 1.7rem;
  }

  h4 {
    font-size: ${props => props.theme.typography.h4FontSize};
  }

  a {
    text-decoration: none;
    font-weight: normal;
    color: inherit;
  }

  p {
    line-height: 1.5rem;
  }

  button {
    border: none;
    background-color: none;
    cursor: pointer;
    outline: none;
    padding: 0;
  }

  #root {
    display: flex;
    min-height: 100vh;
    flex-direction: column;

    & > div:first-of-type {
      flex: 1;
    }
  }
`;
