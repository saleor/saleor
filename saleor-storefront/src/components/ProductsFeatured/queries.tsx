import gql from "graphql-tag";

import { TypedQuery } from "../../core/queries";
import { basicProductFragment } from "../../views/Product/queries";
import { ProductsList } from "./types/ProductsList";

export const featuredProducts = gql`
  ${basicProductFragment}
  query ProductsList {
    shop {
      homepageCollection {
        id
        products(first: 20) {
          edges {
            node {
              ...BasicProductFields
              price {
                amount
                currency
                localized
              }
              category {
                id
                name
              }
            }
          }
        }
      }
    }
  }
`;

export const TypedFeaturedProductsQuery = TypedQuery<ProductsList, {}>(
  featuredProducts
);
