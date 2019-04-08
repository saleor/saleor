import { stringify as stringifyQs } from "qs";
import * as urlJoin from "url-join";

export enum TranslatableEntities {
  categories = "categories",
  products = "products",
  collections = "collections",
  sales = "sales",
  vouchers = "vouchers",
  pages = "pages",
  productTypes = "productTypes"
}

const translationsSection = "/translations/";

export const languageListPath = translationsSection;
export const languageListUrl = translationsSection;

export const languageEntitiesPath = (code: string) =>
  urlJoin(translationsSection, code);
export const languageEntitiesUrl = (code: string, tab?: TranslatableEntities) =>
  languageEntitiesPath(code) +
  "?" +
  stringifyQs({
    tab
  });

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
