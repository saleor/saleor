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

export const attributeFragment = gql`
  fragment AttributeFragment on Attribute {
    id
    name
    slug
    values {
      id
      name
      slug
    }
  }
`;
export const productTypeFragment = gql`
  fragment ProductTypeFragment on ProductType {
    id
    name
    hasVariants
    isShippingRequired
    taxRate
  }
`;

export const productTypeDetailsFragment = gql`
  ${attributeFragment}
  ${productTypeFragment}
  fragment ProductTypeDetailsFragment on ProductType {
    ...ProductTypeFragment
    productAttributes {
      ...AttributeFragment
    }
    variantAttributes {
      ...AttributeFragment
    }
  }
`;

export const TypedProductTypeListQuery = Query as React.ComponentType<
  QueryProps<ProductTypeList, ProductTypeListVariables>
>;
export const productTypeListQuery = gql`
  ${productTypeFragment}
  query ProductTypeList(
    $after: String
    $before: String
    $first: Int
    $last: Int
  ) {
    productTypes(after: $after, before: $before, first: $first, last: $last) {
      edges {
        node {
          ...ProductTypeFragment
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
  ${productTypeDetailsFragment}
  query ProductTypeDetails($id: ID!) {
    productType(id: $id) {
      ...ProductTypeDetailsFragment
    }
  }
`;

export const TypedSearchAttributeQuery = Query as React.ComponentType<
  QueryProps<SearchAttribute, SearchAttributeVariables>
>;
export const searchAttributeQuery = gql`
  ${attributeFragment}
  query SearchAttribute($search: String!) {
    attributes(query: $search, first: 5) {
      edges {
        node {
          ...AttributeFragment
        }
      }
    }
  }
`;
