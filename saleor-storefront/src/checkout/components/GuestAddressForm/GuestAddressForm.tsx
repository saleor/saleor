import * as React from "react";

import { ShippingAddressForm } from "../../../components";
import { getShop_shop } from "../../../components/ShopProvider/types/getShop";
import { maybe } from "../../../core/utils";
import { CheckoutFormType, IGuestAddressProps } from "../../types";
import { Checkout } from "../../types/Checkout";

const getCountryData = (shop: getShop_shop) => {
  const { geolocalization, defaultCountry } = shop;
  return {
    code: maybe(() => geolocalization.country.code, defaultCountry.code),
    country: maybe(
      () => geolocalization.country.country,
      defaultCountry.country
    ),
  };
};

const extractShippingData = (checkout: Checkout | null, shop: getShop_shop) => {
  const country = getCountryData(shop);
  if (!checkout) {
    return { country };
  }

  const checkoutData = checkout && {
    ...checkout.shippingAddress,
    email: checkout.email,
  };

  const hasShippingCountry = !!maybe(() => checkout.shippingAddress.country);
  if (hasShippingCountry) {
    return checkoutData;
  }

  return { ...checkoutData, country };
};

const extractBillingData = (
  checkout: Checkout,
  shop: getShop_shop,
  shippingAsBilling: boolean
) => {
  const addressKey = shippingAsBilling ? "shippingAddress" : "billingAddress";
  const billingAddress = maybe(() => checkout[addressKey], null);

  return {
    country: getCountryData(shop),
    ...billingAddress,
  };
};

const extractData = (
  type: CheckoutFormType,
  checkout: Checkout,
  shop: getShop_shop,
  shippingAsBilling: boolean
) =>
  type === "billing"
    ? extractBillingData(checkout, shop, shippingAsBilling)
    : extractShippingData(checkout, shop);

const GuestAddressForm: React.FC<IGuestAddressProps> = ({
  buttonText,
  checkout,
  errors,
  loading,
  proceedToNextStep,
  shippingAsBilling,
  shop,
  type = "shipping",
}) => (
  <ShippingAddressForm
    type={type as CheckoutFormType}
    data={extractData(
      type as CheckoutFormType,
      checkout,
      shop,
      shippingAsBilling
    )}
    buttonText={buttonText}
    errors={errors}
    loading={loading}
    shippingAsBilling={shippingAsBilling}
    onSubmit={proceedToNextStep}
  />
);

export default GuestAddressForm;
