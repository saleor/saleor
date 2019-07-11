import * as React from "react";
import { RouteComponentProps } from "react-router";

import { CartContext } from "../../../components/CartProvider/context";
import { ShopContext } from "../../../components/ShopProvider/context";
import { UserContext } from "../../../components/User/context";
import { maybe } from "../../../core/utils";
import { CheckoutContext } from "../../context";
import { TypedCreateCheckoutMutation } from "../../queries";
import Page from "./Page";
import { TypedUpdateCheckoutShippingAddressMutation } from "./queries";

class View extends React.Component<RouteComponentProps<{ token?: string }>> {
  render() {
    const {
      history,
      match: {
        params: { token },
      },
    } = this.props;

    return (
      <CheckoutContext.Consumer>
        {({ update, checkout }) => (
          <ShopContext.Consumer>
            {shop => (
              <TypedCreateCheckoutMutation>
                {createCheckout => (
                  <TypedUpdateCheckoutShippingAddressMutation>
                    {updateCheckout => (
                      <CartContext.Consumer>
                        {({ lines }) => (
                          <UserContext.Consumer>
                            {({ user }) => (
                              <Page
                                checkoutId={maybe(() => checkout.id, null)}
                                checkout={checkout}
                                createCheckout={createCheckout}
                                shop={shop}
                                update={update}
                                updateCheckout={updateCheckout}
                                user={user}
                                proceedToNextStepData={{
                                  history,
                                  token,
                                  update,
                                }}
                                lines={lines}
                              />
                            )}
                          </UserContext.Consumer>
                        )}
                      </CartContext.Consumer>
                    )}
                  </TypedUpdateCheckoutShippingAddressMutation>
                )}
              </TypedCreateCheckoutMutation>
            )}
          </ShopContext.Consumer>
        )}
      </CheckoutContext.Consumer>
    );
  }
}

export default View;
