import { MutationFn, MutationResult } from "react-apollo";
import { ConfirmButtonTransitionState } from "./components/ConfirmButton/ConfirmButton";
import { AddressType } from "./customers/types";
import i18n from "./i18n";
import { PartialMutationProviderOutput, UserError } from "./types";
import {
  AuthorizationKeyType,
  OrderStatus,
  PaymentChargeStatusEnum,
  TaxRateType
} from "./types/globalTypes";

export type RequireAtLeastOne<T, Keys extends keyof T = keyof T> = Pick<
  T,
  Exclude<keyof T, Keys>
> &
  { [K in Keys]-?: Required<Pick<T, K>> }[Keys];

export type RequireOnlyOne<T, Keys extends keyof T = keyof T> = Pick<
  T,
  Exclude<keyof T, Keys>
> &
  {
    [K in Keys]-?: Required<Pick<T, K>> &
      Partial<Record<Exclude<Keys, K>, undefined>>
  }[Keys];

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

export function decimal(value: string | number) {
  if (typeof value === "string") {
    return value === "" ? null : value;
  }
  return value;
}

export const removeDoubleSlashes = (url: string) =>
  url.replace(/([^:]\/)\/+/g, "$1");

export const transformPaymentStatus = (status: string) => {
  switch (status) {
    case PaymentChargeStatusEnum.PARTIALLY_CHARGED:
      return { localized: i18n.t("Partially paid"), status: "error" };
    case PaymentChargeStatusEnum.FULLY_CHARGED:
      return { localized: i18n.t("Fully paid"), status: "success" };
    case PaymentChargeStatusEnum.PARTIALLY_REFUNDED:
      return { localized: i18n.t("Partially refunded"), status: "error" };
    case PaymentChargeStatusEnum.FULLY_REFUNDED:
      return { localized: i18n.t("Fully refunded"), status: "success" };
    default:
      return { localized: i18n.t("Unpaid"), status: "error" };
  }
};

export const transformOrderStatus = (status: string) => {
  switch (status) {
    case OrderStatus.FULFILLED:
      return { localized: i18n.t("Fulfilled"), status: "success" };
    case OrderStatus.PARTIALLY_FULFILLED:
      return { localized: i18n.t("Partially fulfilled"), status: "neutral" };
    case OrderStatus.UNFULFILLED:
      return { localized: i18n.t("Unfulfilled"), status: "error" };
    case OrderStatus.CANCELED:
      return { localized: i18n.t("Cancelled"), status: "error" };
    case OrderStatus.DRAFT:
      return { localized: i18n.t("Draft"), status: "error" };
  }
  return {
    localized: status,
    status: "error"
  };
};

export const transformAddressToForm = (data: AddressType) => ({
  city: maybe(() => data.city, ""),
  cityArea: maybe(() => data.cityArea, ""),
  companyName: maybe(() => data.companyName, ""),
  country: {
    label: maybe(() => data.country.country, ""),
    value: maybe(() => data.country.code, "")
  },
  countryArea: maybe(() => data.countryArea, ""),
  firstName: maybe(() => data.firstName, ""),
  lastName: maybe(() => data.lastName, ""),
  phone: maybe(() => data.phone, ""),
  postalCode: maybe(() => data.postalCode, ""),
  streetAddress1: maybe(() => data.streetAddress1, ""),
  streetAddress2: maybe(() => data.streetAddress2, "")
});

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

export function only<T>(obj: T, key: keyof T): boolean {
  return Object.keys(obj).every(objKey =>
    objKey === key ? obj[key] !== undefined : obj[key] === undefined
  );
}

export function empty(obj: object): boolean {
  return Object.keys(obj).every(key => obj[key] === undefined);
}

export function hasErrors(errorList: UserError[] | null): boolean {
  return !(
    errorList === undefined ||
    errorList === null ||
    errorList.length === 0
  );
}

export function getMutationState(
  called: boolean,
  loading: boolean,
  ...errorList: UserError[][]
): ConfirmButtonTransitionState {
  if (loading) {
    return "loading";
  }
  if (called) {
    return errorList.map(hasErrors).reduce((acc, curr) => acc || curr, false)
      ? "error"
      : "success";
  }
  return "default";
}

export function getMutationProviderData<TData, TVariables>(
  mutateFn: MutationFn<TData, TVariables>,
  opts: MutationResult<TData>
): PartialMutationProviderOutput<TData, TVariables> {
  return {
    mutate: variables => mutateFn({ variables }),
    opts
  };
}

interface User {
  email: string;
  firstName?: string;
  lastName?: string;
}

export function getUserName(user?: User, returnEmail?: boolean) {
  return user && (user.email || (user.firstName && user.lastName))
    ? user.firstName && user.lastName
      ? [user.firstName, user.lastName].join(" ")
      : returnEmail
      ? user.email
      : user.email.split("@")[0]
    : undefined;
}

export function getUserInitials(user?: User) {
  return user && (user.email || (user.firstName && user.lastName))
    ? (user.firstName && user.lastName
        ? user.firstName[0] + user.lastName[0]
        : user.email.slice(0, 2)
      ).toUpperCase()
    : undefined;
}
