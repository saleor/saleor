import "./scss/index.scss";

import { History } from "history";
import * as React from "react";
import { AlertManager, useAlert } from "react-alert";
import { generatePath, RouteComponentProps } from "react-router";
import { Link } from "react-router-dom";

import { Button, CartTable } from "../../../components";

import { CartContext } from "../../../components/CartProvider/context";
import { extractCheckoutLines } from "../../../components/CartProvider/uitls";
import { UserContext } from "../../../components/User/context";
import { orderConfirmationUrl } from "../../../routes";
import { StepCheck } from "../../components";
import { CheckoutContext } from "../../context";
import { paymentUrl } from "../../routes";
import { TypedCompleteCheckoutMutation } from "./queries";
import Summary from "./Summary";
import { completeCheckout } from "./types/completeCheckout";

const completeCheckout = (
  data: completeCheckout,
  history: History,
  guest: boolean,
  clearCheckout: () => void,
  clearCart: () => void,
  alert: AlertManager
) => {
  const canProceed = !data.checkoutComplete.errors.length;

  if (canProceed) {
    const { id, token } = data.checkoutComplete.order;
    history.push({
      pathname: orderConfirmationUrl,
      state: guest ? { token } : { id },
    });
    clearCheckout();
    clearCart();
    alert.show(
      { title: "Your order was placed" },
      {
        type: "success",
      }
    );
  } else {
    data.checkoutComplete.errors.map(error => {
      alert.show(
        { title: error.message },
        {
          type: "error",
        }
      );
    });
  }
};

const View: React.FC<RouteComponentProps<{ token?: string }>> = ({
  history,
  match: {
    path,
    params: { token },
  },
}) => {
  const alert = useAlert();
  const {
    cardData,
    dummyStatus,
    checkout,
    clear: clearCheckout,
    step,
  } = React.useContext(CheckoutContext);
  const { clear: clearCart } = React.useContext(CartContext);
  const user = React.useContext(UserContext);

  const stepCheck = (
    <StepCheck checkout={checkout} step={step} path={path} token={token} />
  );

  if (!checkout) {
    return stepCheck;
  }

  return (
    <>
      {stepCheck}
      <div className="checkout-review">
        <Link
          to={generatePath(paymentUrl, { token })}
          className="checkout-review__back"
        >
          Go back to the previous Step
        </Link>

        <div className="checkout__step checkout__step--inactive">
          <span>5</span>
          <h4 className="checkout__header">Review your order</h4>
        </div>

        <div className="checkout__content">
          <CartTable
            lines={extractCheckoutLines(checkout.lines)}
            subtotal={checkout.subtotalPrice.gross.localized}
            deliveryCost={checkout.shippingMethod.price.localized}
            totalCost={checkout.totalPrice.gross.localized}
          />
          <div className="checkout-review__content">
            <Summary
              checkout={checkout}
              cardData={cardData}
              dummyStatus={dummyStatus}
            />
            <div className="checkout-review__content__submit">
              <TypedCompleteCheckoutMutation
                onCompleted={data =>
                  completeCheckout(
                    data,
                    history,
                    !user,
                    clearCheckout,
                    clearCart,
                    alert
                  )
                }
              >
                {(completeCheckout, { loading }) => (
                  <Button
                    type="submit"
                    disabled={loading}
                    onClick={() =>
                      completeCheckout({
                        variables: {
                          checkoutId: checkout.id,
                        },
                      })
                    }
                  >
                    {loading ? "Loading" : "Place your order"}
                  </Button>
                )}
              </TypedCompleteCheckoutMutation>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default View;
