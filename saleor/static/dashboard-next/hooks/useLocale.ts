import { useContext } from "react";

import { LocaleContext } from "../components/Locale";

function useLocale() {
  const themeInfo = useContext(LocaleContext);
  return themeInfo;
}
export default useLocale;
