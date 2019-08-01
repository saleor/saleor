import gql from "graphql-tag";

import { TypedMutation } from "@saleor/mutations";
import { attributeDetailsFragment } from "./queries";
import {
  AttributeBulkDelete,
  AttributeBulkDeleteVariables
} from "./types/AttributeBulkDelete";
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
  AttributeValueCreate,
  AttributeValueCreateVariables
} from "./types/AttributeValueCreate";
import {
  AttributeValueDelete,
  AttributeValueDeleteVariables
} from "./types/AttributeValueDelete";
import {
  AttributeValueReorder,
  AttributeValueReorderVariables
} from "./types/AttributeValueReorder";
import {
  AttributeValueUpdate,
  AttributeValueUpdateVariables
} from "./types/AttributeValueUpdate";

const attributeBulkDelete = gql`
  mutation AttributeBulkDelete($ids: [ID!]!) {
    attributeBulkDelete(ids: $ids) {
      errors {
        field
        message
      }
    }
  }
`;
export const AttributeBulkDeleteMutation = TypedMutation<
  AttributeBulkDelete,
  AttributeBulkDeleteVariables
>(attributeBulkDelete);

const attributeDelete = gql`
  mutation AttributeDelete($id: ID!) {
    attributeDelete(id: $id) {
      errors {
        field
        message
      }
    }
  }
`;
export const AttributeDeleteMutation = TypedMutation<
  AttributeDelete,
  AttributeDeleteVariables
>(attributeDelete);

export const attributeUpdateMutation = gql`
  ${attributeDetailsFragment}
  mutation AttributeUpdate($id: ID!, $input: AttributeUpdateInput!) {
    attributeUpdate(id: $id, input: $input) {
      errors {
        field
        message
      }
      attribute {
        ...AttributeDetailsFragment
      }
    }
  }
`;
export const AttributeUpdateMutation = TypedMutation<
  AttributeUpdate,
  AttributeUpdateVariables
>(attributeUpdateMutation);

const attributeValueDelete = gql`
  ${attributeDetailsFragment}
  mutation AttributeValueDelete($id: ID!) {
    attributeValueDelete(id: $id) {
      errors {
        field
        message
      }
      attribute {
        ...AttributeDetailsFragment
      }
    }
  }
`;
export const AttributeValueDeleteMutation = TypedMutation<
  AttributeValueDelete,
  AttributeValueDeleteVariables
>(attributeValueDelete);

export const attributeValueUpdateMutation = gql`
  ${attributeDetailsFragment}
  mutation AttributeValueUpdate($id: ID!, $input: AttributeValueCreateInput!) {
    attributeValueUpdate(id: $id, input: $input) {
      errors {
        field
        message
      }
      attribute {
        ...AttributeDetailsFragment
      }
    }
  }
`;
export const AttributeValueUpdateMutation = TypedMutation<
  AttributeValueUpdate,
  AttributeValueUpdateVariables
>(attributeValueUpdateMutation);

export const attributeValueCreateMutation = gql`
  ${attributeDetailsFragment}
  mutation AttributeValueCreate($id: ID!, $input: AttributeValueCreateInput!) {
    attributeValueCreate(attribute: $id, input: $input) {
      errors {
        field
        message
      }
      attribute {
        ...AttributeDetailsFragment
      }
    }
  }
`;
export const AttributeValueCreateMutation = TypedMutation<
  AttributeValueCreate,
  AttributeValueCreateVariables
>(attributeValueCreateMutation);

export const attributeCreateMutation = gql`
  ${attributeDetailsFragment}
  mutation AttributeCreate($input: AttributeCreateInput!) {
    attributeCreate(input: $input) {
      errors {
        field
        message
      }
      attribute {
        ...AttributeDetailsFragment
      }
    }
  }
`;
export const AttributeCreateMutation = TypedMutation<
  AttributeCreate,
  AttributeCreateVariables
>(attributeCreateMutation);

const attributeValueReorderMutation = gql`
  mutation AttributeValueReorder($id: ID!, $move: ReorderInput!) {
    attributeReorderValues(attributeId: $id, moves: [$move]) {
      errors {
        field
        message
      }
      attribute {
        id
        values {
          id
        }
      }
    }
  }
`;
export const AttributeValueReorderMutation = TypedMutation<
  AttributeValueReorder,
  AttributeValueReorderVariables
>(attributeValueReorderMutation);
