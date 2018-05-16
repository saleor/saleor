import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../images/placeholder60x60.png";
import OrderSummary from "../../../orders/components/OrderSummary";
import {
  countries,
  order as orderFixture,
  prefixes
} from "../../../orders/fixtures";
import Decorator from "../../Decorator";

const order = orderFixture(placeholderImage);

storiesOf("Orders / OrderSummary", module)
  .addDecorator(Decorator)
  .add("when loading data", () => <OrderSummary />)
  .add("order unfulfilled", () => (
    <OrderSummary
      products={order.products}
      subtotal={order.subtotal}
      total={order.total}
      status={"unfulfilled"}
      paymentStatus={order.paymentStatus}
      paid={order.payment.paid}
      refunded={order.payment.refunded}
      net={order.payment.net}
      onRowClick={() => {}}
      onFulfill={() => {}}
      onCapture={() => {}}
      onRefund={() => {}}
      onRelease={() => {}}
      onOrderCancel={() => {}}
    />
  ))
  .add("order partially fulfilled", () => (
    <OrderSummary
      products={order.products}
      subtotal={order.subtotal}
      total={order.total}
      status={"partially fulfilled"}
      paymentStatus={order.paymentStatus}
      paid={order.payment.paid}
      refunded={order.payment.refunded}
      net={order.payment.net}
      onRowClick={() => {}}
      onFulfill={() => {}}
      onCapture={() => {}}
      onRefund={() => {}}
      onRelease={() => {}}
      onOrderCancel={() => {}}
    />
  ))
  .add("order fulfilled", () => (
    <OrderSummary
      products={order.products}
      subtotal={order.subtotal}
      total={order.total}
      status={"fulfilled"}
      paymentStatus={order.paymentStatus}
      paid={order.payment.paid}
      refunded={order.payment.refunded}
      net={order.payment.net}
      onRowClick={() => {}}
      onFulfill={() => {}}
      onCapture={() => {}}
      onRefund={() => {}}
      onRelease={() => {}}
      onOrderCancel={() => {}}
    />
  ))
  .add("order cancelled", () => (
    <OrderSummary
      products={order.products}
      subtotal={order.subtotal}
      total={order.total}
      status={"cancelled"}
      paymentStatus={order.paymentStatus}
      paid={order.payment.paid}
      refunded={order.payment.refunded}
      net={order.payment.net}
      onRowClick={() => {}}
      onFulfill={() => {}}
      onCapture={() => {}}
      onRefund={() => {}}
      onRelease={() => {}}
      onOrderCancel={() => {}}
    />
  ))
  .add("order draft", () => (
    <OrderSummary
      products={order.products}
      subtotal={order.subtotal}
      total={order.total}
      paymentStatus={order.paymentStatus}
      status={"draft"}
      paid={order.payment.paid}
      refunded={order.payment.refunded}
      net={order.payment.net}
      onRowClick={() => {}}
      onFulfill={() => {}}
      onCapture={() => {}}
      onRefund={() => {}}
      onRelease={() => {}}
      onOrderCancel={() => {}}
    />
  ))
  .add("payment confirmed", () => (
    <OrderSummary
      products={order.products}
      subtotal={order.subtotal}
      total={order.total}
      paymentStatus="confirmed"
      status={order.status}
      paid={order.payment.paid}
      refunded={order.payment.refunded}
      net={order.payment.net}
      onRowClick={() => {}}
      onFulfill={() => {}}
      onCapture={() => {}}
      onRefund={() => {}}
      onRelease={() => {}}
      onOrderCancel={() => {}}
    />
  ))
  .add("payment error", () => (
    <OrderSummary
      products={order.products}
      subtotal={order.subtotal}
      total={order.total}
      paymentStatus="error"
      status={order.status}
      paid={order.payment.paid}
      refunded={order.payment.refunded}
      net={order.payment.net}
      onRowClick={() => {}}
      onFulfill={() => {}}
      onCapture={() => {}}
      onRefund={() => {}}
      onRelease={() => {}}
      onOrderCancel={() => {}}
    />
  ))
  .add("payment input", () => (
    <OrderSummary
      products={order.products}
      subtotal={order.subtotal}
      total={order.total}
      paymentStatus="input"
      status={order.status}
      paid={order.payment.paid}
      refunded={order.payment.refunded}
      net={order.payment.net}
      onRowClick={() => {}}
      onFulfill={() => {}}
      onCapture={() => {}}
      onRefund={() => {}}
      onRelease={() => {}}
      onOrderCancel={() => {}}
    />
  ))
  .add("payment preauth", () => (
    <OrderSummary
      products={order.products}
      subtotal={order.subtotal}
      total={order.total}
      paymentStatus="preauth"
      status={order.status}
      paid={order.payment.paid}
      refunded={order.payment.refunded}
      net={order.payment.net}
      onRowClick={() => {}}
      onFulfill={() => {}}
      onCapture={() => {}}
      onRefund={() => {}}
      onRelease={() => {}}
      onOrderCancel={() => {}}
    />
  ))
  .add("payment refunded", () => (
    <OrderSummary
      products={order.products}
      subtotal={order.subtotal}
      total={order.total}
      paymentStatus="refunded"
      status={order.status}
      paid={order.payment.paid}
      refunded={order.payment.refunded}
      net={order.payment.net}
      onRowClick={() => {}}
      onFulfill={() => {}}
      onCapture={() => {}}
      onRefund={() => {}}
      onRelease={() => {}}
      onOrderCancel={() => {}}
    />
  ))
  .add("payment rejected", () => (
    <OrderSummary
      products={order.products}
      subtotal={order.subtotal}
      total={order.total}
      paymentStatus="rejected"
      status={order.status}
      paid={order.payment.paid}
      refunded={order.payment.refunded}
      net={order.payment.net}
      onRowClick={() => {}}
      onFulfill={() => {}}
      onCapture={() => {}}
      onRefund={() => {}}
      onRelease={() => {}}
      onOrderCancel={() => {}}
    />
  ))
  .add("payment waiting", () => (
    <OrderSummary
      products={order.products}
      subtotal={order.subtotal}
      total={order.total}
      paymentStatus="waiting"
      status={order.status}
      paid={order.payment.paid}
      refunded={order.payment.refunded}
      net={order.payment.net}
      onRowClick={() => {}}
      onFulfill={() => {}}
      onCapture={() => {}}
      onRefund={() => {}}
      onRelease={() => {}}
      onOrderCancel={() => {}}
    />
  ));
