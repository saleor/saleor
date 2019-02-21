import gql from "graphql-tag";

import { TypedQuery } from "../queries";
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

const shippingZones = gql`
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
    }
  }
`;
export const TypedShippingZones = TypedQuery<
  ShippingZones,
  ShippingZonesVariables
>(shippingZones);
