import * as i18n from "i18next";
import * as XHR from "i18next-xhr-backend";
import * as LanguageDetector from "i18next-browser-languagedetector";

i18n.use(XHR);
i18n.use(LanguageDetector);
i18n.init({
  debug: true,
  defaultNS: "dashboard",
  fallbackLng: "en",
  keySeparator: false,
  ns: ["dashboard"],
  nsSeparator: false,
  interpolation: {
    escapeValue: false
  }
});

export default i18n;
