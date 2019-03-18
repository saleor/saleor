import MuiThemeProvider from "@material-ui/core/styles/MuiThemeProvider";
import * as React from "react";

import Baseline from "../../Baseline";
import createTheme, { IThemeColors } from "../../theme";

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
  gray: {
    default: "#202124",
    disabled: "rgba(32, 33, 36, 0.6)"
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
  gray: {
    default: "#C8C8C8",
    disabled: "rgba(216, 216, 216, 0.3)"
  },
  paperBorder: "#EAEAEA",
  primary: "#13BEBB",
  secondary: "#13BEBB"
};

interface IThemeContext {
  isDark: boolean;
  toggleTheme: () => void;
}
export const ThemeContext = React.createContext<IThemeContext>(undefined);

interface ThemeProviderProps {
  isDefaultDark?: boolean;
}
const ThemeProvider: React.FC<ThemeProviderProps> = ({
  children,
  isDefaultDark
}) => {
  const [isDark, setDark] = React.useState(isDefaultDark);

  return (
    <ThemeContext.Provider
      value={{
        isDark,
        toggleTheme: () => setDark(!isDark)
      }}
    >
      <MuiThemeProvider theme={createTheme(isDark ? dark : light)}>
        <Baseline />
        {children}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  );
};
ThemeProvider.defaultProps = {
  isDefaultDark: false
};
export default ThemeProvider;
