import gql from "graphql-tag";

import { TypedMutation } from "../mutations";
import {
  ProductTypeCreate,
  ProductTypeCreateVariables
} from "./types/ProductTypeCreate";
import {
  ProductTypeDelete,
  ProductTypeDeleteVariables
} from "./types/ProductTypeDelete";
import {
  ProductTypeUpdate,
  ProductTypeUpdateVariables
} from "./types/ProductTypeUpdate";

export const productTypeDeleteMutation = gql`
  mutation ProductTypeDelete($id: ID!) {
    productTypeDelete(id: $id) {
      errors {
        field
        message
      }
      productType {
        id
      }
    }
  }
`;
export const TypedProductTypeDeleteMutation = TypedMutation<
  ProductTypeDelete,
  ProductTypeDeleteVariables
>(productTypeDeleteMutation);

export const productTypeUpdateMutation = gql`
  mutation ProductTypeUpdate($id: ID!, $input: ProductTypeInput!) {
    productTypeUpdate(id: $id, input: $input) {
      errors {
        field
        message
      }
      productType {
        id
        name
        hasVariants
        taxRate
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
      }
    }
  }
`;
export const TypedProductTypeUpdateMutation = TypedMutation<
  ProductTypeUpdate,
  ProductTypeUpdateVariables
>(productTypeUpdateMutation);

export const productTypeCreateMutation = gql`
  mutation ProductTypeCreate($input: ProductTypeInput!) {
    productTypeCreate(input: $input) {
      errors {
        field
        message
      }
      productType {
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
      }
    }
  }
`;
export const TypedProductTypeCreateMutation = TypedMutation<
  ProductTypeCreate,
  ProductTypeCreateVariables
>(productTypeCreateMutation);
