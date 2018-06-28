import gql from "graphql-tag";
import { Mutation, MutationProps } from "react-apollo";

import {
  PageCreateMutation,
  PageCreateMutationVariables,
  PageDeleteMutation,
  PageDeleteMutationVariables,
  PageUpdateMutation,
  PageUpdateMutationVariables
} from "../gql-types";

export const TypedPageDeleteMutation = Mutation as React.ComponentType<
  MutationProps<PageDeleteMutation, PageDeleteMutationVariables>
  >;
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

export const TypedPageUpdateMutation = Mutation as React.ComponentType<
  MutationProps<PageUpdateMutation, PageUpdateMutationVariables>
  >;
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

export const TypedPageCreateMutation = Mutation as React.ComponentType<
  MutationProps<PageCreateMutation, PageCreateMutationVariables>
  >;
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
