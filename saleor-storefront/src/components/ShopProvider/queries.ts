import gql from "graphql-tag";

import { TypedQuery } from "../../core/queries";
import { getShop } from "./types/getShop";

const getShopQuery = gql`
  query getShop {
    shop {
      defaultCountry {
        code
        country
      }
      countries {
        country
        code
      }
      geolocalization {
        country {
          code
          country
        }
      }
    }
  }
`;

export const TypedGetShopQuery = TypedQuery<getShop, {}>(getShopQuery);
