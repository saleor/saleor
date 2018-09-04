import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../images/placeholder60x60.png";
import OrderSummary from "../../../orders/components/OrderSummary";
import { order as orderFixture } from "../../../orders/fixtures";
import Decorator from "../../Decorator";

const order = orderFixture(placeholderImage);
const callbacks = {
  onCapture: undefined,
  onCreate: undefined,
  onFulfill: undefined,
  onOrderCancel: undefined,
  onOrderLineChange: () => () => undefined,
  onOrderLineRemove: () => undefined,
  onRefund: undefined,
  onRelease: undefined,
  onRowClick: () => undefined
};

storiesOf("Orders / OrderSummary", module)
  .addDecorator(Decorator)
  .add("when loading data", () => <OrderSummary />)
  .add("order unfulfilled", () => (
    <OrderSummary
      net={order.payment.net}
      paid={order.payment.paid}
      paymentStatus={order.paymentStatus}
      products={order.products}
      refunded={order.payment.refunded}
      status={"unfulfilled"}
      subtotal={order.subtotal}
      total={order.total}
      {...callbacks}
    />
  ))
  .add("order partially fulfilled", () => (
    <OrderSummary
      net={order.payment.net}
      paid={order.payment.paid}
      paymentStatus={order.paymentStatus}
      products={order.products}
      refunded={order.payment.refunded}
      status={"partially fulfilled"}
      subtotal={order.subtotal}
      total={order.total}
      {...callbacks}
    />
  ))
  .add("order fulfilled", () => (
    <OrderSummary
      net={order.payment.net}
      paid={order.payment.paid}
      paymentStatus={order.paymentStatus}
      products={order.products}
      refunded={order.payment.refunded}
      status={"fulfilled"}
      subtotal={order.subtotal}
      total={order.total}
      {...callbacks}
    />
  ))
  .add("order cancelled", () => (
    <OrderSummary
      net={order.payment.net}
      paid={order.payment.paid}
      paymentStatus={order.paymentStatus}
      products={order.products}
      refunded={order.payment.refunded}
      status={"cancelled"}
      subtotal={order.subtotal}
      total={order.total}
      {...callbacks}
    />
  ))
  .add("order draft", () => (
    <OrderSummary
      net={order.payment.net}
      paid={order.payment.paid}
      paymentStatus={order.paymentStatus}
      products={order.products}
      refunded={order.payment.refunded}
      status={"draft"}
      subtotal={order.subtotal}
      total={order.total}
      {...callbacks}
    />
  ))
  .add("payment confirmed", () => (
    <OrderSummary
      net={order.payment.net}
      paid={order.payment.paid}
      paymentStatus="confirmed"
      products={order.products}
      refunded={order.payment.refunded}
      status={order.status}
      subtotal={order.subtotal}
      total={order.total}
      {...callbacks}
    />
  ))
  .add("payment error", () => (
    <OrderSummary
      net={order.payment.net}
      paid={order.payment.paid}
      paymentStatus="error"
      products={order.products}
      refunded={order.payment.refunded}
      status={order.status}
      subtotal={order.subtotal}
      total={order.total}
      {...callbacks}
    />
  ))
  .add("payment input", () => (
    <OrderSummary
      net={order.payment.net}
      paid={order.payment.paid}
      paymentStatus="input"
      products={order.products}
      refunded={order.payment.refunded}
      status={order.status}
      subtotal={order.subtotal}
      total={order.total}
      {...callbacks}
    />
  ))
  .add("payment preauth", () => (
    <OrderSummary
      net={order.payment.net}
      paid={order.payment.paid}
      paymentStatus="preauth"
      products={order.products}
      refunded={order.payment.refunded}
      status={order.status}
      subtotal={order.subtotal}
      total={order.total}
      {...callbacks}
    />
  ))
  .add("payment refunded", () => (
    <OrderSummary
      net={order.payment.net}
      paid={order.payment.paid}
      paymentStatus="refunded"
      products={order.products}
      refunded={order.payment.refunded}
      status={order.status}
      subtotal={order.subtotal}
      total={order.total}
      {...callbacks}
    />
  ))
  .add("payment rejected", () => (
    <OrderSummary
      net={order.payment.net}
      paid={order.payment.paid}
      paymentStatus="rejected"
      products={order.products}
      refunded={order.payment.refunded}
      status={order.status}
      subtotal={order.subtotal}
      total={order.total}
      {...callbacks}
    />
  ))
  .add("payment waiting", () => (
    <OrderSummary
      net={order.payment.net}
      paid={order.payment.paid}
      paymentStatus="waiting"
      products={order.products}
      refunded={order.payment.refunded}
      status={order.status}
      subtotal={order.subtotal}
      total={order.total}
      {...callbacks}
    />
  ));
