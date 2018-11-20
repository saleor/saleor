import * as urlJoin from "url-join";

import { orderUrl } from "../../urls";

export const orderCancelUrl = (id: string) => urlJoin(orderUrl(id), "cancel");
export const orderMarkAsPaidUrl = (id: string) =>
  urlJoin(orderUrl(id), "markAsPaid");
export const orderPaymentVoidUrl = (id: string) =>
  urlJoin(orderUrl(id), "voidPayment");
export const orderPaymentRefundUrl = (id: string) =>
  urlJoin(orderUrl(id), "refundPayment");
export const orderPaymentCaptureUrl = (id: string) =>
  urlJoin(orderUrl(id), "capturePayment");
export const orderFulfillUrl = (id: string) => urlJoin(orderUrl(id), "fulfill");
export const orderFulfillmentCancelUrl = (
  orderId: string,
  fulfillmentId: string
) => urlJoin(orderUrl(orderId), "fulfillment", fulfillmentId, "cancel");
export const orderFulfillmentEditTrackingUrl = (
  orderId: string,
  fulfillmentId: string
) => urlJoin(orderUrl(orderId), "fulfillment", fulfillmentId, "tracking");
export const orderBillingAddressEditUrl = (id: string) =>
  urlJoin(orderUrl(id), "editAddress", "billing");
export const orderShippingAddressEditUrl = (id: string) =>
  urlJoin(orderUrl(id), "editAddress", "shipping");
