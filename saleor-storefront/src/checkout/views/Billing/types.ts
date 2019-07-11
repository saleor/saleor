import { History } from "history";
import { MutationFn } from "react-apollo";

import { getShop_shop } from "../../../components/ShopProvider/types/getShop";
import { User } from "../../../components/User/types/User";
import { FormError } from "../../../core/types";
import { CheckoutContextInterface, CheckoutStep } from "../../context";
import { Checkout } from "../../types/Checkout";
import {
  updateCheckoutBillingAddress,
  updateCheckoutBillingAddressVariables
} from "./types/updateCheckoutBillingAddress";

export interface IBillingPageProps {
  checkoutId?: string;
  checkout?: Checkout;
  update: (checkoutData: CheckoutContextInterface) => void;
  saveBillingAddress: MutationFn<
    updateCheckoutBillingAddress,
    updateCheckoutBillingAddressVariables
  >;
  shippingAsBilling: boolean;
  user: User;
  path: string;
  shop: getShop_shop;
  step: CheckoutStep;
  proceedToNextStepData: {
    update: (checkoutData: CheckoutContextInterface) => void;
    history: History;
    token?: string;
  };
  validateStep: boolean;
}

export interface IBillingPageState {
  checkout: Checkout;
  errors: FormError[];
  loading: boolean;
}
