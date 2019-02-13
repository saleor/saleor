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
    $isPublished: Boolean!
    $publicationDate: String
  ) {
    pageUpdate(
      id: $id
      input: {
        title: $title
        content: $content
        slug: $slug
        isPublished: $isPublished
        publicationDate: $publicationDate
      }
    ) {
      page {
        id
        slug
        title
        content
        isPublished
        publicationDate
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
    $isPublished: Boolean!
    $publicationDate: String
  ) {
    pageCreate(
      input: {
        title: $title
        content: $content
        slug: $slug
        isPublished: $isPublished
        publicationDate: $publicationDate
      }
    ) {
      page {
        id
        slug
        title
        content
        isPublished
        publicationDate
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
