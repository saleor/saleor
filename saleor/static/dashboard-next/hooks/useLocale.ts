import { useContext } from "react";

import { LocaleContext } from "@saleor-components/Locale";

function useLocale() {
  const themeInfo = useContext(LocaleContext);
  return themeInfo;
}
export default useLocale;
