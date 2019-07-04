import gql from "graphql-tag";

import { pageInfoFragment, TypedQuery } from "../queries";
import { ShippingZone, ShippingZoneVariables } from "./types/ShippingZone";
import { ShippingZones, ShippingZonesVariables } from "./types/ShippingZones";

export const shippingZoneFragment = gql`
  fragment ShippingZoneFragment on ShippingZone {
    id
    countries {
      code
      country
    }
    name
  }
`;
export const shippingMethodFragment = gql`
  fragment ShippingMethodFragment on ShippingMethod {
    id
    minimumOrderPrice {
      amount
      currency
    }
    minimumOrderWeight {
      unit
      value
    }
    maximumOrderPrice {
      amount
      currency
    }
    maximumOrderWeight {
      unit
      value
    }
    name
    price {
      amount
      currency
    }
    type
  }
`;
export const shippingZoneDetailsFragment = gql`
  ${shippingZoneFragment}
  ${shippingMethodFragment}
  fragment ShippingZoneDetailsFragment on ShippingZone {
    ...ShippingZoneFragment
    default
    shippingMethods {
      ...ShippingMethodFragment
    }
  }
`;

const shippingZones = gql`
  ${pageInfoFragment}
  ${shippingZoneFragment}
  query ShippingZones(
    $first: Int
    $after: String
    $last: Int
    $before: String
  ) {
    shippingZones(first: $first, after: $after, last: $last, before: $before) {
      edges {
        node {
          ...ShippingZoneFragment
        }
      }
      pageInfo {
        ...PageInfoFragment
      }
    }
  }
`;
export const TypedShippingZones = TypedQuery<
  ShippingZones,
  ShippingZonesVariables
>(shippingZones);

const shippingZone = gql`
  ${shippingZoneDetailsFragment}
  query ShippingZone($id: ID!) {
    shippingZone(id: $id) {
      ...ShippingZoneDetailsFragment
    }
  }
`;
export const TypedShippingZone = TypedQuery<
  ShippingZone,
  ShippingZoneVariables
>(shippingZone);
