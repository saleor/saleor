import * as urlJoin from "url-join";

const translationsSection = "/translations/";

export const languageListPath = translationsSection;
export const languageListUrl = translationsSection;

export const languageEntitiesPath = (code: string) =>
  urlJoin(translationsSection, code);
export const languageEntitiesUrl = languageEntitiesPath;

export enum TranslatableEntities {
  categories = "categories",
  products = "products"
}

export const languageEntityPath = (
  code: string,
  entity: TranslatableEntities,
  id: string
) => urlJoin(languageEntitiesPath(code), entity.toString(), id);
export const languageEntityUrl = (
  code: string,
  entity: TranslatableEntities,
  id: string
) => languageEntityPath(code, entity, encodeURIComponent(id));
