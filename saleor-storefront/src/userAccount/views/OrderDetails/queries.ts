import gql from "graphql-tag";
import { TypedQuery } from "../../../core/queries";

import {
  checkoutAddressFragment,
  checkoutProductVariantFragment
} from "../../../checkout/queries";
import { OrderById, OrderByIdVariables } from "./types/OrderById";
import { OrderByToken, OrderByTokenVariables } from "./types/OrderByToken";

const orderPriceFragment = gql`
  fragment OrderPrice on TaxedMoney {
    gross {
      localized
    }
  }
`;

const orderDetailFragment = gql`
  ${orderPriceFragment}
  ${checkoutAddressFragment}
  ${checkoutProductVariantFragment}
  fragment OrderDetail on Order {
    userEmail
    paymentStatus
    paymentStatusDisplay
    status
    statusDisplay
    id
    number
    shippingAddress {
      ...Address
    }
    lines {
      productName
      quantity
      variant {
        ...ProductVariant
      }
      unitPrice {
        currency
        gross {
          amount
        }
      }
    }
    subtotal {
      ...OrderPrice
    }
    total {
      ...OrderPrice
    }
    shippingPrice {
      ...OrderPrice
    }
  }
`;

const orderDetailsByIdQuery = gql`
  ${orderDetailFragment}
  query OrderById($id: ID!) {
    order(id: $id) {
      ...OrderDetail
    }
  }
`;

const orderDetailsByTokenQuery = gql`
  ${orderDetailFragment}
  query OrderByToken($token: String!) {
    orderByToken(token: $token) {
      ...OrderDetail
    }
  }
`;

export const TypedOrderDetailsByIdQuery = TypedQuery<
  OrderById,
  OrderByIdVariables
>(orderDetailsByIdQuery);

export const TypedOrderDetailsByTokenQuery = TypedQuery<
  OrderByToken,
  OrderByTokenVariables
>(orderDetailsByTokenQuery);
