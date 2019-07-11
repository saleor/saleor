import * as React from "react";
import { generatePath, Redirect, RouteComponentProps } from "react-router";

import { BASE_URL } from "../../core/config";
import { CheckoutContext, CheckoutStep } from "../context";
import {
  billingUrl,
  paymentUrl,
  reviewUrl,
  shippingAddressUrl,
  shippingOptionsUrl
} from "../routes";

const getRedirectUrl = (token: string, step: CheckoutStep): string => {
  const generatedPath = (path: string) => generatePath(path, { token });

  switch (step) {
    case CheckoutStep.ShippingAddress:
      return generatedPath(shippingAddressUrl);

    case CheckoutStep.ShippingOption:
      return generatedPath(shippingOptionsUrl);

    case CheckoutStep.BillingAddress:
      return generatedPath(billingUrl);

    case CheckoutStep.Payment:
      return generatedPath(paymentUrl);

    case CheckoutStep.Review:
      return generatedPath(reviewUrl);

    default:
      return BASE_URL;
  }
};

const CheckoutDispatcher: React.FC<RouteComponentProps<{ token?: string }>> = ({
  match: {
    params: { token },
  },
}) => (
  <CheckoutContext.Consumer>
    {({ step }) => <Redirect to={getRedirectUrl(token, step)} />}
  </CheckoutContext.Consumer>
);

export default CheckoutDispatcher;
