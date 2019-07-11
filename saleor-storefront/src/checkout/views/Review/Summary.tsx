import * as React from "react";
import ReactSVG from "react-svg";

import { AddressSummary } from "../../../components";
import { CardData } from "../../context";
import { Checkout } from "../../types/Checkout";

import copyImg from "../../../images/copy.svg";

class Summary extends React.PureComponent<{
  checkout: Checkout;
  cardData: CardData;
  dummyStatus: string;
}> {
  shippingAddressRef: React.RefObject<HTMLParagraphElement> = React.createRef();
  billingAddressRef: React.RefObject<HTMLParagraphElement> = React.createRef();
  shippingMethodRef: React.RefObject<HTMLParagraphElement> = React.createRef();
  paymentMethodRef: React.RefObject<HTMLParagraphElement> = React.createRef();

  copyHandler = (ref: React.RefObject<HTMLParagraphElement>) => () => {
    const selection = window.getSelection();
    const range = document.createRange();

    range.selectNodeContents(ref.current);
    selection.removeAllRanges();
    selection.addRange(range);
    document.execCommand("copy");
    selection.removeAllRanges();
  };

  render() {
    const { checkout, cardData, dummyStatus } = this.props;

    return (
      <div className="checkout-review__content__summary">
        <div>
          <h4>
            Shipping address
            <ReactSVG
              className="checkout-review__summary-copy"
              path={copyImg}
              onClick={this.copyHandler(this.shippingAddressRef)}
            />
          </h4>
          <AddressSummary
            address={checkout.shippingAddress}
            email={checkout.email}
            paragraphRef={this.shippingAddressRef}
          />
        </div>
        <div>
          <h4>
            Billing address
            <ReactSVG
              className="checkout-review__summary-copy"
              onClick={this.copyHandler(this.billingAddressRef)}
              path={copyImg}
            />
          </h4>
          <AddressSummary
            address={checkout.billingAddress}
            paragraphRef={this.billingAddressRef}
          />
        </div>
        <div>
          <h4>
            Shipping method
            <ReactSVG
              className="checkout-review__summary-copy"
              onClick={this.copyHandler(this.shippingMethodRef)}
              path={copyImg}
            />
          </h4>
          <p ref={this.shippingMethodRef}>{checkout.shippingMethod.name}</p>
        </div>
        <div>
          <h4>
            Payment method
            <ReactSVG
              className="checkout-review__summary-copy"
              onClick={this.copyHandler(this.paymentMethodRef)}
              path={copyImg}
            />
          </h4>
          <p ref={this.paymentMethodRef}>
            {!!cardData
              ? `Ending in ${cardData.lastDigits}`
              : `Dummy: ${dummyStatus}`}
          </p>
        </div>
      </div>
    );
  }
}

export default Summary;
