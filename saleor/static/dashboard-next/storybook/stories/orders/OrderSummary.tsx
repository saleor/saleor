import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../images/placeholder60x60.png";
import OrderSummary from "../../../orders/components/OrderSummary";
import { order as orderFixture } from "../../../orders/fixtures";
import { OrderStatus } from "../../../types/globalTypes";
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

const shippingPrice = {
  gross: {
    amount: 9123.12,
    currency: "USD"
  }
};

storiesOf("Orders / OrderSummary", module)
  .addDecorator(Decorator)
  .add("when loading data", () => <OrderSummary {...callbacks} />)
  .add("order unfulfilled", () => (
    <OrderSummary
      paid={order.payment.paid}
      paymentStatus={order.paymentStatus}
      lines={order.products}
      shippingMethodName="DHL"
      shippingPrice={shippingPrice}
      status={OrderStatus.UNFULFILLED}
      subtotal={order.subtotal}
      total={order.total}
      {...callbacks}
    />
  ))
  .add("order partially fulfilled", () => (
    <OrderSummary
      paid={order.payment.paid}
      paymentStatus={order.paymentStatus}
      lines={order.products}
      shippingMethodName="DHL"
      shippingPrice={shippingPrice}
      status={OrderStatus.PARTIALLY_FULFILLED}
      subtotal={order.subtotal}
      total={order.total}
      {...callbacks}
    />
  ))
  .add("order fulfilled", () => (
    <OrderSummary
      paid={order.payment.paid}
      paymentStatus={order.paymentStatus}
      lines={order.products}
      shippingMethodName="DHL"
      shippingPrice={shippingPrice}
      status={OrderStatus.FULFILLED}
      subtotal={order.subtotal}
      total={order.total}
      {...callbacks}
    />
  ))
  .add("order cancelled", () => (
    <OrderSummary
      paid={order.payment.paid}
      paymentStatus={order.paymentStatus}
      lines={order.products}
      shippingMethodName="DHL"
      shippingPrice={shippingPrice}
      status={OrderStatus.CANCELED}
      subtotal={order.subtotal}
      total={order.total}
      {...callbacks}
    />
  ))
  .add("order draft", () => (
    <OrderSummary
      paid={order.payment.paid}
      paymentStatus={order.paymentStatus}
      lines={order.products}
      shippingMethodName="DHL"
      shippingPrice={shippingPrice}
      status={OrderStatus.DRAFT}
      subtotal={order.subtotal}
      total={order.total}
      {...callbacks}
    />
  ))
  .add("payment confirmed", () => (
    <OrderSummary
      paid={order.payment.paid}
      paymentStatus="confirmed"
      lines={order.products}
      shippingMethodName="DHL"
      shippingPrice={shippingPrice}
      status={order.status}
      subtotal={order.subtotal}
      total={order.total}
      {...callbacks}
    />
  ))
  .add("payment error", () => (
    <OrderSummary
      paid={order.payment.paid}
      paymentStatus="error"
      lines={order.products}
      shippingMethodName="DHL"
      shippingPrice={shippingPrice}
      status={order.status}
      subtotal={order.subtotal}
      total={order.total}
      {...callbacks}
    />
  ))
  .add("payment input", () => (
    <OrderSummary
      paid={order.payment.paid}
      paymentStatus="input"
      lines={order.products}
      shippingMethodName="DHL"
      shippingPrice={shippingPrice}
      status={order.status}
      subtotal={order.subtotal}
      total={order.total}
      {...callbacks}
    />
  ))
  .add("payment preauth", () => (
    <OrderSummary
      paid={order.payment.paid}
      paymentStatus="preauth"
      lines={order.products}
      shippingMethodName="DHL"
      shippingPrice={shippingPrice}
      status={order.status}
      subtotal={order.subtotal}
      total={order.total}
      {...callbacks}
    />
  ))
  .add("payment refunded", () => (
    <OrderSummary
      paid={order.payment.paid}
      paymentStatus="refunded"
      lines={order.products}
      shippingMethodName="DHL"
      shippingPrice={shippingPrice}
      status={order.status}
      subtotal={order.subtotal}
      total={order.total}
      {...callbacks}
    />
  ))
  .add("payment rejected", () => (
    <OrderSummary
      paid={order.payment.paid}
      paymentStatus="rejected"
      lines={order.products}
      shippingMethodName="DHL"
      shippingPrice={shippingPrice}
      status={order.status}
      subtotal={order.subtotal}
      total={order.total}
      {...callbacks}
    />
  ))
  .add("payment waiting", () => (
    <OrderSummary
      paid={order.payment.paid}
      paymentStatus="waiting"
      lines={order.products}
      shippingMethodName="DHL"
      shippingPrice={shippingPrice}
      status={order.status}
      subtotal={order.subtotal}
      total={order.total}
      {...callbacks}
    />
  ));
