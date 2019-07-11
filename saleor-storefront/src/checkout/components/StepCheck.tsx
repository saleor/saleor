import * as React from "react";
import { generatePath, Redirect } from "react-router";

import { CheckoutStep } from "../context";
import {
  baseUrl,
  billingUrl,
  paymentUrl,
  reviewUrl,
  shippingAddressUrl,
  shippingOptionsUrl
} from "../routes";
import { Checkout } from "../types/Checkout";

/**
 * Gets checkout step based on the provided path.
 */
export const getCurrentStep = (path: string, token?: string): CheckoutStep => {
  const generatedPath = path => generatePath(path, { token });

  switch (generatedPath(path)) {
    case generatedPath(shippingAddressUrl):
      return CheckoutStep.ShippingAddress;

    case generatedPath(shippingOptionsUrl):
      return CheckoutStep.ShippingOption;

    case generatedPath(billingUrl):
      return CheckoutStep.BillingAddress;

    case generatedPath(paymentUrl):
      return CheckoutStep.Payment;

    case generatedPath(reviewUrl):
      return CheckoutStep.Review;

    default:
      return CheckoutStep.ShippingAddress;
  }
};

/**
 * Redirector to prevent user from entering invalid step by manually pasting the url.
 */
const StepCheck: React.FC<{
  checkout: Checkout;
  step: CheckoutStep;
  path: string;
  token?: string;
}> = ({ step, checkout, path, token, children }) => {
  if (!checkout || step < getCurrentStep(path, token)) {
    return <Redirect to={baseUrl} />;
  }
  return children ? <>{children}</> : null;
};

export default StepCheck;
