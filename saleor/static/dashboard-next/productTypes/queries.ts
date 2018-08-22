import gql from "graphql-tag";
import { Query, QueryProps } from "react-apollo";

import {
  ProductTypeListQuery,
  ProductTypeListQueryVariables
} from "../gql-types";

export const TypedProductTypeListQuery = Query as React.ComponentType<
  QueryProps<ProductTypeListQuery, ProductTypeListQueryVariables>
>;
export const productTypeListQuery = gql`
  query ProductTypeList(
    $after: String
    $before: String
    $first: Int
    $last: Int
  ) {
    productTypes(after: $after, before: $before, first: $first, last: $last) {
      edges {
        node {
          id
          name
          hasVariants
          productAttributes {
            edges {
              node {
                id
                name
              }
            }
          }
          variantAttributes {
            edges {
              node {
                id
                name
              }
            }
          }
        }
      }
      pageInfo {
        hasNextPage
        hasPreviousPage
        startCursor
        endCursor
      }
    }
  }
`;
