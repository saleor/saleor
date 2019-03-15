import { Theme } from "@material-ui/core/styles";
import MuiThemeProvider from "@material-ui/core/styles/MuiThemeProvider";
import * as React from "react";

import createTheme, { IThemeColors } from "../../theme";

export type ThemeVariant = "dark" | "light";

// TODO: fix secondary buttons lol
const dark: IThemeColors = {
  background: {
    default: "#1D1E1F",
    paper: "#2E2F31"
  },
  error: "#C22D74",
  font: {
    default: "#FCFCFC",
    gray: "#9E9D9D"
  },
  paperBorder: "#252728",
  primary: "#13BEBB",
  secondary: "#13BEBB"
};
const light: IThemeColors = {
  background: {
    default: "#F1F6F6",
    paper: "#FFFFFF"
  },
  error: "#C22D74",
  font: {
    default: "#3D3D3D",
    gray: "#616161"
  },
  paperBorder: "#EAEAEA",
  primary: "#13BEBB",
  secondary: "#13BEBB"
};

interface IThemeContext {
  theme: Theme;
  variant: ThemeVariant;
  setTheme: (variant: ThemeVariant) => void;
}
export const ThemeContext = React.createContext<IThemeContext>(undefined);

interface ThemeProviderProps {
  variant?: ThemeVariant;
}
const ThemeProvider: React.FC<ThemeProviderProps> = ({ children, variant }) => {
  const defaultTheme = createTheme(variant === "dark" ? dark : light);
  const [themeInfo, setTheme] = React.useState({
    muiTheme: defaultTheme,
    variant
  });

  return (
    <ThemeContext.Provider
      value={{
        setTheme: variant =>
          setTheme({
            muiTheme: createTheme(variant === "dark" ? dark : light),
            variant
          }),
        theme: themeInfo.muiTheme,
        variant
      }}
    >
      <MuiThemeProvider theme={themeInfo.muiTheme}>{children}</MuiThemeProvider>
    </ThemeContext.Provider>
  );
};
ThemeProvider.defaultProps = {
  variant: "dark"
};
export default ThemeProvider;
