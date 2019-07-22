import { useContext } from "react";

import { ThemeContext } from "@saleor/components/Theme";

function useTheme() {
  const themeInfo = useContext(ThemeContext);
  return themeInfo;
}
export default useTheme;
