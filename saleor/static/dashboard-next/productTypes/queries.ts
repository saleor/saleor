import gql from "graphql-tag";
import { Query, QueryProps } from "react-apollo";

import {
  ProductTypeDetails,
  ProductTypeDetailsVariables
} from "./types/ProductTypeDetails";
import {
  ProductTypeList,
  ProductTypeListVariables
} from "./types/ProductTypeList";
import {
  SearchAttribute,
  SearchAttributeVariables
} from "./types/SearchAttribute";

export const TypedProductTypeListQuery = Query as React.ComponentType<
  QueryProps<ProductTypeList, ProductTypeListVariables>
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
            id
            name
          }
          variantAttributes {
            id
            name
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
  QueryProps<ProductTypeDetails, ProductTypeDetailsVariables>
>;
export const productTypeDetailsQuery = gql`
  query ProductTypeDetails($id: ID!) {
    productType(id: $id) {
      id
      name
      hasVariants
      productAttributes {
        id
        slug
        name
      }
      variantAttributes {
        id
        slug
        name
      }
      isShippingRequired
      taxRate
    }
  }
`;

export const TypedSearchAttributeQuery = Query as React.ComponentType<
  QueryProps<SearchAttribute, SearchAttributeVariables>
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
