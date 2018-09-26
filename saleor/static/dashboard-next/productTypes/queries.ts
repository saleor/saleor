import gql from "graphql-tag";

import { TypedQuery } from "../queries";
import { ProductTypeCreateData } from "./types/ProductTypeCreateData";
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
    weight {
      unit
      value
    }
  }
`;

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
export const TypedProductTypeListQuery = TypedQuery<
  ProductTypeList,
  ProductTypeListVariables
>(productTypeListQuery);

export const productTypeDetailsQuery = gql`
  ${productTypeDetailsFragment}
  query ProductTypeDetails($id: ID!) {
    productType(id: $id) {
      ...ProductTypeDetailsFragment
    }
    shop {
      defaultWeightUnit
    }
  }
`;
export const TypedProductTypeDetailsQuery = TypedQuery<
  ProductTypeDetails,
  ProductTypeDetailsVariables
>(productTypeDetailsQuery);

export const productTypeCreateDataQuery = gql`
  query ProductTypeCreateData {
    shop {
      defaultWeightUnit
    }
  }
`;
export const TypedProductTypeCreateDataQuery = TypedQuery<
  ProductTypeCreateData,
  {}
>(productTypeCreateDataQuery);

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
export const TypedSearchAttributeQuery = TypedQuery<
  SearchAttribute,
  SearchAttributeVariables
>(searchAttributeQuery);
