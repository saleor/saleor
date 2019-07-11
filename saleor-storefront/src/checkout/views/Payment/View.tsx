import "./scss/index.scss";

import * as React from "react";
import { MutationFn } from "react-apollo";
import { generatePath, RouteComponentProps } from "react-router";

import { GatewaysEnum } from "../../../../types/globalTypes";
import { Button } from "../../../components";
import { PROVIDERS } from "../../../core/config";
import { maybe } from "../../../core/utils";
import { CartSummary, Option, StepCheck, Steps } from "../../components";
import {
  CheckoutContext,
  CheckoutContextInterface,
  CheckoutStep
} from "../../context";
import { reviewUrl } from "../../routes";
import CreditCard from "./Gateways/Braintree/CreditCard";
import Dummy from "./Gateways/Dummy";
import {
  TypedGetPaymentTokenQuery,
  TypedPaymentMethodCreateMutation
} from "./queries";
import { createPayment, createPaymentVariables } from "./types/createPayment";

export interface ProviderProps {
  loading: boolean;
  formRef: React.RefObject<HTMLFormElement>;
  paymentClientToken: string;
  checkout: CheckoutContextInterface;
  processPayment(token: string, gateway: GatewaysEnum): Promise<void>;
  setLoadingState(loading: boolean): void;
}

class View extends React.Component<
  RouteComponentProps<{ token?: string }>,
  {
    loading: boolean;
    validateStep: boolean;
    selectedGeteway: GatewaysEnum;
  }
> {
  state = {
    loading: false,
    selectedGeteway: null,
    validateStep: true,
  };
  formRef: React.RefObject<HTMLFormElement> = React.createRef();

  setLoadingState = (loading: boolean) => this.setState({ loading });

  proceedNext = (data: createPayment) => {
    const canProceed = !data.checkoutPaymentCreate.errors.length;

    if (canProceed) {
      const {
        history,
        match: {
          params: { token },
        },
      } = this.props;
      this.setState({ loading: false });
      history.push(generatePath(reviewUrl, { token }));
    }
  };

  componentDidMount() {
    this.setState({ validateStep: false });
  }

  processPayment = (
    createPaymentMethod: MutationFn<createPayment, createPaymentVariables>,
    checkout: CheckoutContextInterface
  ) => async (token: string, gateway: GatewaysEnum) => {
    const {
      checkout: { billingAddress, totalPrice, id },
    } = checkout;

    if (token) {
      createPaymentMethod({
        variables: {
          checkoutId: id,
          input: {
            amount: totalPrice.gross.amount,
            billingAddress: {
              city: billingAddress.city,
              country: billingAddress.country.code,
              countryArea: billingAddress.countryArea,
              firstName: billingAddress.firstName,
              lastName: billingAddress.lastName,
              postalCode: billingAddress.postalCode,
              streetAddress1: billingAddress.streetAddress1,
              streetAddress2: billingAddress.streetAddress2,
            },
            gateway,
            token,
          },
        },
      });
    }
  };

  render() {
    const {
      params: { token },
      path,
    } = this.props.match;
    const { selectedGeteway, loading: stateLoding } = this.state;

    return (
      <CheckoutContext.Consumer>
        {checkout =>
          this.state.validateStep ? (
            <StepCheck
              checkout={checkout.checkout}
              step={checkout.step}
              path={path}
              token={token}
            />
          ) : (
            <CartSummary checkout={checkout.checkout}>
              <div className="checkout-payment">
                <Steps
                  step={CheckoutStep.Payment}
                  token={token}
                  checkout={checkout.checkout}
                >
                  <TypedPaymentMethodCreateMutation
                    onCompleted={this.proceedNext}
                  >
                    {(
                      createPaymentMethod,
                      { loading: paymentCreateLoading }
                    ) => (
                      <TypedGetPaymentTokenQuery
                        alwaysRender
                        skip={!selectedGeteway}
                        variables={{ gateway: selectedGeteway }}
                      >
                        {({ data, loading: getTokenLoading }) => {
                          const paymentClientToken = maybe(
                            () => data.paymentClientToken,
                            null
                          );
                          const {
                            availablePaymentGateways,
                          } = checkout.checkout;
                          const processPayment = this.processPayment(
                            createPaymentMethod,
                            checkout
                          );
                          const loading =
                            stateLoding ||
                            getTokenLoading ||
                            paymentCreateLoading;
                          const optionProps = provider => ({
                            key: provider,
                            onSelect: () =>
                              this.setState({ selectedGeteway: provider }),
                            selected: selectedGeteway === provider,
                            value: provider,
                          });
                          const providerProps = {
                            checkout,
                            formRef: this.formRef,
                            loading,
                            paymentClientToken,
                            processPayment,
                            setLoadingState: this.setLoadingState,
                          };

                          return (
                            <div className="checkout-payment__form">
                              {availablePaymentGateways.map(provider => {
                                switch (provider) {
                                  case PROVIDERS.BRAINTREE:
                                    return (
                                      <Option
                                        label="Credit Card"
                                        {...optionProps(provider)}
                                      >
                                        <CreditCard {...providerProps} />
                                      </Option>
                                    );

                                  case PROVIDERS.DUMMY:
                                    return (
                                      <Option
                                        label="Dummy"
                                        {...optionProps(provider)}
                                      >
                                        <Dummy {...providerProps} />
                                      </Option>
                                    );
                                }
                              })}

                              <div>
                                <Button
                                  type="submit"
                                  disabled={loading || !paymentClientToken}
                                  onClick={() => {
                                    this.formRef.current.dispatchEvent(
                                      new Event("submit")
                                    );
                                  }}
                                >
                                  Continue to Review Your Order
                                </Button>
                              </div>
                            </div>
                          );
                        }}
                      </TypedGetPaymentTokenQuery>
                    )}
                  </TypedPaymentMethodCreateMutation>
                </Steps>
              </div>
            </CartSummary>
          )
        }
      </CheckoutContext.Consumer>
    );
  }
}

export default View;
