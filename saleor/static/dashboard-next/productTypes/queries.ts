import gql from "graphql-tag";
import { Query, QueryProps } from "react-apollo";

import {
  ProductTypeCreateDataQuery,
  ProductTypeDetailsQuery,
  ProductTypeDetailsQueryVariables,
  ProductTypeListQuery,
  ProductTypeListQueryVariables,
  SearchAttributeQuery,
  SearchAttributeQueryVariables
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

export const TypedProductTypeDetailsQuery = Query as React.ComponentType<
  QueryProps<ProductTypeDetailsQuery, ProductTypeDetailsQueryVariables>
>;
export const productTypeDetailsQuery = gql`
  query ProductTypeDetails($id: ID!) {
    productType(id: $id) {
      id
      name
      hasVariants
      productAttributes {
        edges {
          node {
            id
            slug
            name
          }
        }
      }
      variantAttributes {
        edges {
          node {
            id
            slug
            name
          }
        }
      }
      isShippingRequired
      taxRate
    }
    shop {
      taxRate(countryCode: "PL") {
        standardRate
        reducedRates {
          rateType
        }
      }
    }
  }
`;

export const TypedProductTypeCreateDataQuery = Query as React.ComponentType<
  QueryProps<ProductTypeCreateDataQuery>
>;
// FIXME: Country code should be supplied from API, not hardcoded
export const productTypeCreateQuery = gql`
  query ProductTypeCreateData {
    shop {
      taxRate(countryCode: "PL") {
        standardRate
        reducedRates {
          rateType
        }
      }
    }
  }
`;

export const TypedSearchAttributeQuery = Query as React.ComponentType<
  QueryProps<SearchAttributeQuery, SearchAttributeQueryVariables>
>;
export const searchAttributeQuery = gql`
  query SearchAttribute($search: String!) {
    attributes(query: $search, first: 5) {
      edges {
        node {
          id
          slug
          name
        }
      }
    }
  }
`;
