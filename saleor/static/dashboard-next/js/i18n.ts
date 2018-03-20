import * as i18n from "i18next";
import * as LanguageDetector from "i18next-browser-languagedetector";
import * as XHR from "i18next-xhr-backend";

i18n.use(XHR);
i18n.use(LanguageDetector);
i18n.init({
  defaultNS: "dashboard",
  fallbackLng: "en",
  interpolation: {
    escapeValue: false
  },
  keySeparator: false,
  ns: ["dashboard"],
  nsSeparator: false
});

export default i18n;
