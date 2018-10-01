import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../images/placeholder60x60.png";
import OrderSummary, {
  OrderSummaryProps
} from "../../../orders/components/OrderSummary";
import { order as orderFixture } from "../../../orders/fixtures";
import { OrderStatus, PaymentStatusEnum } from "../../../types/globalTypes";
import Decorator from "../../Decorator";

const order = orderFixture(placeholderImage);
const props: OrderSummaryProps = {
  authorized: order.totalAuthorized,
  isDraft: order.status === OrderStatus.DRAFT,
  lines: order.lines.edges.map(edge => edge.node),
  onCapture: undefined,
  onCreate: undefined,
  onFulfill: undefined,
  onOrderCancel: undefined,
  onOrderLineChange: () => () => undefined,
  onOrderLineRemove: () => undefined,
  onRefund: undefined,
  onRelease: undefined,
  onRowClick: () => undefined,
  paid: order.totalCaptured,
  paymentStatus: order.paymentStatus,
  shippingMethodName: order.shippingMethodName,
  shippingPrice: order.shippingPrice,
  status: order.status,
  subtotal: order.subtotal.gross,
  total: order.total.gross
};

storiesOf("Orders / OrderSummary", module)
  .addDecorator(Decorator)
  .add("when loading data", () => <OrderSummary {...props} />)
  .add("order unfulfilled", () => (
    <OrderSummary {...props} status={OrderStatus.UNFULFILLED} />
  ))
  .add("order partially fulfilled", () => (
    <OrderSummary {...props} status={OrderStatus.PARTIALLY_FULFILLED} />
  ))
  .add("order fulfilled", () => (
    <OrderSummary {...props} status={OrderStatus.FULFILLED} />
  ))
  .add("order cancelled", () => (
    <OrderSummary {...props} status={OrderStatus.CANCELED} />
  ))
  .add("order draft", () => (
    <OrderSummary {...props} status={OrderStatus.DRAFT} />
  ))
  .add("payment confirmed", () => (
    <OrderSummary {...props} paymentStatus={PaymentStatusEnum.CONFIRMED} />
  ))
  .add("payment error", () => (
    <OrderSummary {...props} paymentStatus={PaymentStatusEnum.ERROR} />
  ))
  .add("payment input", () => (
    <OrderSummary {...props} paymentStatus={PaymentStatusEnum.INPUT} />
  ))
  .add("payment preauth", () => (
    <OrderSummary {...props} paymentStatus={PaymentStatusEnum.PREAUTH} />
  ))
  .add("payment refunded", () => (
    <OrderSummary {...props} paymentStatus={PaymentStatusEnum.REFUNDED} />
  ))
  .add("payment rejected", () => (
    <OrderSummary {...props} paymentStatus={PaymentStatusEnum.REJECTED} />
  ))
  .add("payment waiting", () => (
    <OrderSummary {...props} paymentStatus={PaymentStatusEnum.WAITING} />
  ));
