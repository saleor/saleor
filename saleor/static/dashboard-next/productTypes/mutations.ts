import gql from "graphql-tag";

import { TypedMutation } from "../mutations";
import { attributeFragment, productTypeDetailsFragment } from "./queries";
import {
  AttributeCreate,
  AttributeCreateVariables
} from "./types/AttributeCreate";
import {
  AttributeDelete,
  AttributeDeleteVariables
} from "./types/AttributeDelete";
import {
  AttributeUpdate,
  AttributeUpdateVariables
} from "./types/AttributeUpdate";
import {
  ProductTypeBulkDelete,
  ProductTypeBulkDeleteVariables
} from "./types/ProductTypeBulkDelete";
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

export const productTypeBulkDeleteMutation = gql`
  mutation ProductTypeBulkDelete($ids: [ID]!) {
    productTypeBulkDelete(ids: $ids) {
      errors {
        field
        message
      }
    }
  }
`;
export const TypedProductTypeBulkDeleteMutation = TypedMutation<
  ProductTypeBulkDelete,
  ProductTypeBulkDeleteVariables
>(productTypeBulkDeleteMutation);

export const productTypeUpdateMutation = gql`
  ${productTypeDetailsFragment}
  mutation ProductTypeUpdate($id: ID!, $input: ProductTypeInput!) {
    productTypeUpdate(id: $id, input: $input) {
      errors {
        field
        message
      }
      productType {
        ...ProductTypeDetailsFragment
      }
    }
  }
`;
export const TypedProductTypeUpdateMutation = TypedMutation<
  ProductTypeUpdate,
  ProductTypeUpdateVariables
>(productTypeUpdateMutation);

export const productTypeCreateMutation = gql`
  ${productTypeDetailsFragment}
  mutation ProductTypeCreate($input: ProductTypeInput!) {
    productTypeCreate(input: $input) {
      errors {
        field
        message
      }
      productType {
        ...ProductTypeDetailsFragment
      }
    }
  }
`;
export const TypedProductTypeCreateMutation = TypedMutation<
  ProductTypeCreate,
  ProductTypeCreateVariables
>(productTypeCreateMutation);

export const attributeCreateMutation = gql`
  ${productTypeDetailsFragment}
  mutation AttributeCreate(
    $id: ID!
    $input: AttributeCreateInput!
    $type: AttributeTypeEnum!
  ) {
    attributeCreate(id: $id, input: $input, type: $type) {
      errors {
        field
        message
      }
      productType {
        ...ProductTypeDetailsFragment
      }
    }
  }
`;
export const TypedAttributeCreateMutation = TypedMutation<
  AttributeCreate,
  AttributeCreateVariables
>(attributeCreateMutation);

export const attributeUpdateMutation = gql`
  ${attributeFragment}
  mutation AttributeUpdate($id: ID!, $input: AttributeUpdateInput!) {
    attributeUpdate(id: $id, input: $input) {
      errors {
        field
        message
      }
      attribute {
        ...AttributeFragment
      }
    }
  }
`;
export const TypedAttributeUpdateMutation = TypedMutation<
  AttributeUpdate,
  AttributeUpdateVariables
>(attributeUpdateMutation);

export const attributeDeleteMutation = gql`
  ${productTypeDetailsFragment}
  mutation AttributeDelete($id: ID!) {
    attributeDelete(id: $id) {
      errors {
        field
        message
      }
      productType {
        ...ProductTypeDetailsFragment
      }
    }
  }
`;
export const TypedAttributeDeleteMutation = TypedMutation<
  AttributeDelete,
  AttributeDeleteVariables
>(attributeDeleteMutation);
