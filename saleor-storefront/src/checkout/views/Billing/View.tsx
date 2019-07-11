import * as React from "react";
import { RouteComponentProps } from "react-router";

import { ShopContext } from "../../../components/ShopProvider/context";
import { UserContext } from "../../../components/User/context";
import { maybe } from "../../../core/utils";
import { CheckoutContext } from "../../context";
import Page from "./Page";
import { TypedUpdateCheckoutBillingAddressMutation } from "./queries";

class View extends React.Component<
  RouteComponentProps<{ token?: string }>,
  { validateStep: boolean }
> {
  readonly state = { validateStep: true };

  componentDidMount() {
    this.setState({ validateStep: false });
  }

  render() {
    const {
      history,
      match: {
        path,
        params: { token },
      },
    } = this.props;

    return (
      <CheckoutContext.Consumer>
        {({ update, checkout, shippingAsBilling, step }) => (
          <ShopContext.Consumer>
            {shop => (
              <TypedUpdateCheckoutBillingAddressMutation>
                {saveBillingAddress => (
                  <UserContext.Consumer>
                    {({ user }) => (
                      <Page
                        shippingAsBilling={shippingAsBilling}
                        checkoutId={maybe(() => checkout.id, null)}
                        checkout={checkout}
                        shop={shop}
                        path={path}
                        update={update}
                        saveBillingAddress={saveBillingAddress}
                        step={step}
                        user={user}
                        proceedToNextStepData={{
                          history,
                          token,
                          update,
                        }}
                        validateStep={this.state.validateStep}
                      />
                    )}
                  </UserContext.Consumer>
                )}
              </TypedUpdateCheckoutBillingAddressMutation>
            )}
          </ShopContext.Consumer>
        )}
      </CheckoutContext.Consumer>
    );
  }
}

export default View;
