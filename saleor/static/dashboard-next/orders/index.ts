import i18n from "../i18n";

export interface AddressType {
  city: string;
  cityArea: string;
  companyName: string;
  country: string;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: {
    prefix: string;
    number: string;
  };
  postalCode: string;
  streetAddress_1: string;
  streetAddress_2: string;
}

export const PaymentStatus = {
  CONFIRMED: "confirmed",
  ERROR: "error",
  INPUT: "input",
  PREAUTH: "preauth",
  REFUNDED: "refunded",
  REJECTED: "rejected",
  WAITING: "waiting"
};
export const OrderStatus = {
  CANCELLED: "cancelled",
  DRAFT: "draft",
  FULFILLED: "fulfilled",
  PARTIALLY_FULFILLED: "partially fulfilled",
  UNFULFILLED: "unfulfilled"
};
export const FulfillmentStatus = {
  CANCELLED: "cancelled",
  FULFILLED: "fulfilled"
};
export const PaymentVariants = {
  MANUAL: "manual"
};

export const transformPaymentStatus = (status: string) => {
  switch (status) {
    case PaymentStatus.CONFIRMED:
      return { localized: i18n.t("Confirmed"), status: "success" };
    case PaymentStatus.REFUNDED:
      return { localized: i18n.t("Refunded"), status: "success" };
    case PaymentStatus.WAITING:
      return {
        localized: i18n.t("Waiting for confirmation"),
        status: "neutral"
      };
    case PaymentStatus.PREAUTH:
      return { localized: i18n.t("Preauthorized"), status: "neutral" };
    case PaymentStatus.INPUT:
      return { localized: i18n.t("Input"), status: "neutral" };
    case PaymentStatus.REJECTED:
      return { localized: i18n.t("Rejected"), status: "error" };
    case PaymentStatus.ERROR:
      return { localized: i18n.t("Error"), status: "error" };
  }
  return {
    localized: status,
    status: "error"
  };
};

export const transformOrderStatus = (status: string) => {
  switch (status) {
    case OrderStatus.FULFILLED:
      return { localized: i18n.t("Fulfilled"), status: "success" };
    case OrderStatus.PARTIALLY_FULFILLED:
      return { localized: i18n.t("Partially fulfilled"), status: "neutral" };
    case OrderStatus.UNFULFILLED:
      return { localized: i18n.t("Unfulfilled"), status: "error" };
    case OrderStatus.CANCELLED:
      return { localized: i18n.t("Cancelled"), status: "error" };
    case OrderStatus.DRAFT:
      return { localized: i18n.t("Draft"), status: "error" };
  }
  return {
    localized: status,
    status: "error"
  };
};

export const transformFulfillmentStatus = (status: string) => {
  switch (status) {
    case FulfillmentStatus.FULFILLED:
      return { localized: i18n.t("Fulfilled"), status: "success" };
    case FulfillmentStatus.CANCELLED:
      return { localized: i18n.t("Cancelled"), status: "neutral" };
  }
  return {
    localized: status,
    status: "error"
  };
};

export const transformAddressToForm = (data: AddressType) => ({
  ...data,
  phone: undefined,
  phone_number: data.phone.number,
  phone_prefix: data.phone.prefix
});
