import gql from "graphql-tag";
import * as React from "react";

import { TypedQuery } from "../../queries";
import { ShopInfo } from "./types/ShopInfo";

const shopInfo = gql`
  query ShopInfo {
    shop {
      defaultCountry {
        code
        country
      }
      defaultCurrency
      defaultWeightUnit
      displayGrossPrices
      domain {
        host
        url
      }
      includeTaxesInPrices
      name
      trackInventoryByDefault
    }
  }
`;
export const TypedShopInfoQuery = TypedQuery<ShopInfo, {}>(shopInfo);
