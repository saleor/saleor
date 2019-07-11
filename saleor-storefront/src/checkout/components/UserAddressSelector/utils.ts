import { each, isEqual, omit, uniqWith } from "lodash";
import { maybe } from "../../../core/utils";
import { IInitialUserAddressesArgs } from "../../types";

export const getInitialAddresses = ({
  type,
  checkout,
  user,
}: IInitialUserAddressesArgs) => {
  const {
    addresses: userAddresses,
    defaultBillingAddress,
    defaultShippingAddress,
  } = user;

  return uniqWith(
    each(
      [
        ...(type === "shipping"
          ? [maybe(() => checkout.shippingAddress, defaultShippingAddress)]
          : [maybe(() => checkout.billingAddress, defaultBillingAddress)]),
        ...userAddresses,
      ].filter(address => address),
      address => omit(address, "id")
    ),
    isEqual
  );
};
