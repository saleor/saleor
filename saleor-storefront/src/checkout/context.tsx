import { createContext } from "react";

import { Checkout } from "./types/Checkout";

export enum CheckoutStep {
  ShippingAddress = 1,
  ShippingOption,
  BillingAddress,
  Payment,
  Review,
}

export interface CardData {
  lastDigits: string;
  ccType: string;
  token: string;
}

export interface CheckoutContextInterface {
  syncWithCart?: boolean;
  syncUserCheckout?: boolean;
  dummyStatus?: string;
  cardData?: CardData;
  checkout?: Checkout;
  loading?: boolean;
  shippingAsBilling?: boolean;
  step?: CheckoutStep;
  update?(checkoutData: CheckoutContextInterface): Promise<void>;
  clear?(): void;
}

export const defaultContext = {
  cardData: null,
  checkout: null,
  clear: () => null,
  dummyStatus: null,
  loading: false,
  shippingAsBilling: false,
  step: CheckoutStep.ShippingAddress,
  syncUserCheckout: false,
  syncWithCart: false,
  update: (checkoutData: {}) => null,
};

export const CheckoutContext = createContext<CheckoutContextInterface>(
  defaultContext
);

CheckoutContext.displayName = "CheckoutContext";
