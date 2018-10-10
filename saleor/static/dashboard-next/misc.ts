import { stringify } from "qs";
import i18n from "./i18n";
import { AuthorizationKeyType, TaxRateType } from "./types/globalTypes";

export interface PageInfo {
  endCursor: string;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string;
}
interface PaginationState {
  after?: string;
  before?: string;
  first?: number;
  last?: number;
}

interface QueryString {
  after?: string;
  before?: string;
}

export function createPaginationState(
  paginateBy: number,
  queryString: QueryString
): PaginationState {
  return queryString && (queryString.before || queryString.after)
    ? queryString.after
      ? {
          after: queryString.after,
          first: paginateBy
        }
      : {
          before: queryString.before,
          last: paginateBy
        }
    : {
        first: paginateBy
      };
}

export function createPaginationData(
  navigate: ((url: string, push: boolean) => void),
  paginationState: PaginationState,
  url: string,
  pageInfo: PageInfo,
  loading
) {
  const loadNextPage = () => {
    if (loading) {
      return;
    }
    return navigate(
      url +
        "?" +
        stringify({
          after: encodeURIComponent(pageInfo.endCursor)
        }),
      true
    );
  };
  const loadPreviousPage = () => {
    if (loading) {
      return;
    }
    return navigate(
      url +
        "?" +
        stringify({
          before: encodeURIComponent(pageInfo.startCursor)
        }),
      true
    );
  };
  const newPageInfo = pageInfo
    ? {
        ...pageInfo,
        hasNextPage: !!paginationState.before || pageInfo.hasNextPage,
        hasPreviousPage: !!paginationState.after || pageInfo.hasPreviousPage
      }
    : undefined;

  return {
    loadNextPage,
    loadPreviousPage,
    pageInfo: newPageInfo
  };
}

export function renderCollection<T>(
  collection: T[],
  renderItem: (
    item: T | undefined,
    index: number | undefined,
    collection: T[]
  ) => any,
  renderEmpty?: (collection: T[]) => any
) {
  if (collection === undefined) {
    return renderItem(undefined, undefined, collection);
  }
  if (collection.length === 0) {
    return !!renderEmpty ? renderEmpty(collection) : null;
  }
  return collection.map(renderItem);
}

export function decimal(value: string) {
  return value === "" ? null : value;
}

export const removeDoubleSlashes = (url: string) =>
  url.replace(/([^:]\/)\/+/g, "$1");

export const translatedTaxRates = () => ({
  [TaxRateType.ACCOMMODATION]: i18n.t("Accommodation"),
  [TaxRateType.ADMISSION_TO_CULTURAL_EVENTS]: i18n.t(
    "Admission to cultural events"
  ),
  [TaxRateType.ADMISSION_TO_ENTERTAINMENT_EVENTS]: i18n.t(
    "Admission to entertainment events"
  ),
  [TaxRateType.ADMISSION_TO_SPORTING_EVENTS]: i18n.t(
    "Admission to sporting events"
  ),
  [TaxRateType.ADVERTISING]: i18n.t("Advertising"),
  [TaxRateType.AGRICULTURAL_SUPPLIES]: i18n.t("Agricultural supplies"),
  [TaxRateType.BABY_FOODSTUFFS]: i18n.t("Baby foodstuffs"),
  [TaxRateType.BIKES]: i18n.t("Bikes"),
  [TaxRateType.BOOKS]: i18n.t("Books"),
  [TaxRateType.CHILDRENS_CLOTHING]: i18n.t("Children's clothing"),
  [TaxRateType.DOMESTIC_FUEL]: i18n.t("Domestic fuel"),
  [TaxRateType.DOMESTIC_SERVICES]: i18n.t("Domestic services"),
  [TaxRateType.E_BOOKS]: i18n.t("E-books"),
  [TaxRateType.FOODSTUFFS]: i18n.t("Foodstuffs"),
  [TaxRateType.HOTELS]: i18n.t("Hotels"),
  [TaxRateType.MEDICAL]: i18n.t("Medical"),
  [TaxRateType.NEWSPAPERS]: i18n.t("Newspapers"),
  [TaxRateType.PASSENGER_TRANSPORT]: i18n.t("Passenger transport"),
  [TaxRateType.PHARMACEUTICALS]: i18n.t("Pharmaceuticals"),
  [TaxRateType.PROPERTY_RENOVATIONS]: i18n.t("Property renovations"),
  [TaxRateType.RESTAURANTS]: i18n.t("Restaurants"),
  [TaxRateType.SOCIAL_HOUSING]: i18n.t("Social housing"),
  [TaxRateType.STANDARD]: i18n.t("Standard"),
  [TaxRateType.WATER]: i18n.t("Water")
});

export const translatedAuthorizationKeyTypes = () => ({
  [AuthorizationKeyType.FACEBOOK]: i18n.t("Facebook"),
  [AuthorizationKeyType.GOOGLE_OAUTH2]: i18n.t("Google OAuth2")
});

export function maybe<T>(exp: () => T, d?: T) {
  try {
    const result = exp();
    return result === undefined ? d : result;
  } catch {
    return d;
  }
}
