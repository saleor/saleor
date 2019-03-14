/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: OrderLineFragment
// ====================================================

export interface OrderLineFragment_unitPrice_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderLineFragment_unitPrice_net {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderLineFragment_unitPrice {
  __typename: "TaxedMoney";
  gross: OrderLineFragment_unitPrice_gross;
  net: OrderLineFragment_unitPrice_net;
}

export interface OrderLineFragment {
  __typename: "OrderLine";
  id: string;
  isShippingRequired: boolean;
  productName: string;
  productSku: string;
  quantity: number;
  quantityFulfilled: number;
  unitPrice: OrderLineFragment_unitPrice | null;
  thumbnailUrl: string | null;
}
