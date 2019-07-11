import * as React from "react";
import { Link } from "react-router-dom";

import { AddressSummary, CartTable, NotFound } from "../../../components";
import { LineI } from "../../../components/CartTable/ProductRow";
import { priceToString } from "../../../core/utils";
import { OrderById_order, OrderById_order_lines } from "./types/OrderById";
import {
  OrderByToken_orderByToken,
  OrderByToken_orderByToken_lines
} from "./types/OrderByToken";

import { orderHistoryUrl } from "../../routes";

const extractOrderLines = (
  lines: Array<OrderById_order_lines | OrderByToken_orderByToken_lines>
): LineI[] => {
  return lines
    .map(line => ({
      quantity: line.quantity,
      totalPrice: priceToString({
        amount: line.quantity * line.unitPrice.gross.amount,
        currency: line.unitPrice.currency,
      }),
      ...line.variant,
      name: line.productName,
    }))
    .sort((a, b) => b.id.toLowerCase().localeCompare(a.id.toLowerCase()));
};

const Page: React.FC<{
  guest: boolean;
  order: OrderById_order | OrderByToken_orderByToken;
}> = ({ guest, order }) =>
  order ? (
    <>
      {!guest && (
        <Link className="order-details__link" to={orderHistoryUrl}>
          Go back to Order History
        </Link>
      )}
      <h3>Your order nr: {order.number}</h3>
      <p className="order-details__status">
        {order.paymentStatusDisplay} / {order.statusDisplay}
      </p>
      <CartTable
        lines={extractOrderLines(order.lines)}
        totalCost={order.total.gross.localized}
        deliveryCost={order.shippingPrice.gross.localized}
        subtotal={order.subtotal.gross.localized}
      />
      <div className="order-details__summary">
        <div>
          <h4>Shipping Address</h4>
          <AddressSummary
            address={order.shippingAddress}
            email={order.userEmail}
            paragraphRef={this.shippingAddressRef}
          />
        </div>
      </div>
    </>
  ) : (
    <NotFound />
  );

export default Page;
