import * as React from "react";
import { generatePath } from "react-router";

import {
  FormAddressType,
  OverlayContext,
  OverlayTheme,
  OverlayType
} from "../../../components";
import { CartLineInterface } from "../../../components/CartProvider/context";
import { findFormErrors, maybe } from "../../../core/utils";
import {
  CartSummary,
  GuestAddressForm,
  ShippingUnavailableModal,
  Steps,
  UserAddressSelector
} from "../../components";
import { CheckoutStep } from "../../context";
import { shippingOptionsUrl } from "../../routes";
import { ICheckoutData, ICheckoutUserArgs } from "../../types";
import { IShippingPageProps, IShippingPageState } from "./types";

const computeCheckoutData = (
  data: FormAddressType,
  lines?: CartLineInterface[],
  email?: string
): ICheckoutData => ({
  email: data.email || email,
  shippingAddress: {
    city: data.city,
    companyName: data.companyName,
    country: data.country.value || data.country.code,
    countryArea: data.countryArea,
    firstName: data.firstName,
    lastName: data.lastName,
    phone: data.phone,
    postalCode: data.postalCode,
    streetAddress1: data.streetAddress1,
    streetAddress2: data.streetAddress2,
  },
  ...(lines && {
    lines: lines.map(({ quantity, variantId }) => ({
      quantity,
      variantId,
    })),
  }),
});

class Page extends React.Component<IShippingPageProps, IShippingPageState> {
  readonly state = {
    checkout: null,
    errors: [],
    loading: false,
    shippingUnavailable: false,
  };

  proceedToShippingOptions = () => {
    const { update, history, token } = this.props.proceedToNextStepData;
    const canProceed =
      !this.state.errors.length && !this.state.shippingUnavailable;

    if (canProceed) {
      if (this.state.shippingUnavailable) {
        return this.renderShippingUnavailableModal();
      }
      update({
        checkout: this.state.checkout || this.props.checkout,
      });
      history.push(
        generatePath(shippingOptionsUrl, {
          token,
        })
      );
    }
  };

  onProceedToShippingSubmit = async (formData: FormAddressType) => {
    await this.onSubmitHandler(formData);
    this.proceedToShippingOptions();
  };

  onShippingSubmit = (address: FormAddressType): Promise<any> => {
    const {
      checkoutId,
      createCheckout,
      user,
      lines,
      update,
      updateCheckout,
    } = this.props;
    const email = maybe(() => user.email, null);
    update({
      shippingAsBilling: maybe(() => address.asBilling, false),
    });

    if (!checkoutId) {
      return createCheckout({
        variables: {
          checkoutInput: computeCheckoutData(address, lines),
        },
      });
    }
    return updateCheckout({
      variables: {
        checkoutId,
        ...computeCheckoutData(address, null, email),
      },
    });
  };

  onSubmitHandler = async (address: FormAddressType) => {
    this.setState({ loading: true });

    await this.onShippingSubmit(address).then(response => {
      const errors = findFormErrors(response);
      const checkout =
        maybe(() => response.data.checkoutEmailUpdate.checkout, null) ||
        maybe(
          () => response.data.checkoutShippingAddressUpdate.checkout,
          null
        ) ||
        maybe(() => response.data.checkoutCreate.checkout, null);

      this.setState({
        checkout,
        errors,
        loading: false,
        shippingUnavailable:
          (checkout && !checkout.availableShippingMethods.length) || false,
      });
    });
    return;
  };

  renderShippingUnavailableModal = () => (
    <OverlayContext.Consumer>
      {overlay => (
        <>
          {overlay.show(OverlayType.modal, OverlayTheme.modal, {
            content: <ShippingUnavailableModal hide={overlay.hide} />,
          })}
          ;
        </>
      )}
    </OverlayContext.Consumer>
  );

  getShippingProps = (userCheckoutData: ICheckoutUserArgs) => ({
    buttonText: "Continue to Shipping",
    errors: this.state.errors,
    loading: this.state.loading,
    proceedToNextStep: this.onProceedToShippingSubmit,
    ...userCheckoutData,
  });

  render() {
    const { checkout, proceedToNextStepData, shop, user, update } = this.props;
    const shippingProps = this.getShippingProps({
      checkout,
      user,
    });

    return (
      <CartSummary checkout={checkout}>
        <div className="checkout-shipping">
          <Steps
            step={CheckoutStep.ShippingAddress}
            token={proceedToNextStepData.token}
            checkout={checkout}
          >
            {user ? (
              <UserAddressSelector
                {...shippingProps}
                update={update}
                onSubmit={this.onSubmitHandler}
                type="shipping"
              />
            ) : (
              <GuestAddressForm {...shippingProps} shop={shop} />
            )}
          </Steps>
        </div>
      </CartSummary>
    );
  }
}

export default Page;
