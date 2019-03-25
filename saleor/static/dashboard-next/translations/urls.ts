import * as urlJoin from "url-join";

const translationsSection = "/translations/";

export const languageListPath = translationsSection;
export const languageListUrl = translationsSection;

export const languageEntitiesPath = (code: string) =>
  urlJoin(translationsSection, code);
export const languageEntitiesUrl = languageEntitiesPath;

// export const language
