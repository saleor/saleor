import gql from "graphql-tag";

import { attributeFragment } from "@saleor/attributes/queries";
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

export const productTypeFragment = gql`
  fragment ProductTypeFragment on ProductType {
    id
    name
    hasVariants
    isShippingRequired
    taxType {
      description
      taxCode
    }
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
    taxTypes {
      taxCode
      description
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
    taxTypes {
      taxCode
      description
    }
  }
`;
export const TypedProductTypeCreateDataQuery = TypedQuery<
  ProductTypeCreateData,
  {}
>(productTypeCreateDataQuery);
