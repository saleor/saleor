import gql from "graphql-tag";

import { TypedMutation } from "../mutations";

import {
  PageCreateMutation,
  PageCreateMutationVariables,
  PageDeleteMutation,
  PageDeleteMutationVariables,
  PageUpdateMutation,
  PageUpdateMutationVariables
} from "../gql-types";

export const pageDeleteMutation = gql`
  mutation PageDelete($id: ID!) {
    pageDelete(id: $id) {
      errors {
        field
        message
      }
    }
  }
`;
export const TypedPageDeleteMutation = TypedMutation<
  PageDeleteMutation,
  PageDeleteMutationVariables
>(pageDeleteMutation);

export const pageUpdateMutation = gql`
  mutation PageUpdate(
    $id: ID!
    $title: String!
    $content: String!
    $slug: String!
    $isVisible: Boolean!
    $availableOn: String
  ) {
    pageUpdate(
      id: $id
      input: {
        title: $title
        content: $content
        slug: $slug
        isVisible: $isVisible
        availableOn: $availableOn
      }
    ) {
      page {
        id
        slug
        title
        content
        isVisible
        availableOn
      }
      errors {
        field
        message
      }
    }
  }
`;
export const TypedPageUpdateMutation = TypedMutation<
  PageUpdateMutation,
  PageUpdateMutationVariables
>(pageUpdateMutation);

export const pageCreateMutation = gql`
  mutation PageCreate(
    $title: String!
    $content: String!
    $slug: String!
    $isVisible: Boolean!
    $availableOn: String
  ) {
    pageCreate(
      input: {
        title: $title
        content: $content
        slug: $slug
        isVisible: $isVisible
        availableOn: $availableOn
      }
    ) {
      page {
        id
        slug
        title
        content
        isVisible
        availableOn
        created
      }
      errors {
        field
        message
      }
    }
  }
`;
export const TypedPageCreateMutation = TypedMutation<
  PageCreateMutation,
  PageCreateMutationVariables
>(pageCreateMutation);
