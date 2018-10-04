import gql from "graphql-tag";

import { TypedMutation } from "../mutations";

import { PageCreate, PageCreateVariables } from "./types/PageCreate";
import { PageDelete, PageDeleteVariables } from "./types/PageDelete";
import { PageUpdate, PageUpdateVariables } from "./types/PageUpdate";

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
  PageDelete,
  PageDeleteVariables
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
  PageUpdate,
  PageUpdateVariables
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
  PageCreate,
  PageCreateVariables
>(pageCreateMutation);
