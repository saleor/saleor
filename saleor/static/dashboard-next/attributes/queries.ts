import gql from "graphql-tag";

import { pageInfoFragment, TypedQuery } from "../queries";
import {
  AttributeDetails,
  AttributeDetailsVariables
} from "./types/AttributeDetails";
import { AttributeList, AttributeListVariables } from "./types/AttributeList";

export const attributeFragment = gql`
  fragment AttributeFragment on Attribute {
    id
    name
    slug
  }
`;

export const attributeDetailsFragment = gql`
  ${attributeFragment}
  fragment AttributeDetailsFragment on Attribute {
    ...AttributeFragment
    inputType
    values {
      id
      name
      slug
      sortOrder
      type
      value
    }
  }
`;

const attributeDetails = gql`
  ${attributeDetailsFragment}
  query AttributeDetails($id: ID!) {
    attribute(id: $id) {
      ...AttributeDetailsFragment
    }
  }
`;
export const AttributeDetailsQuery = TypedQuery<
  AttributeDetails,
  AttributeDetailsVariables
>(attributeDetails);

const attributeList = gql`
  ${attributeFragment}
  ${pageInfoFragment}
  query AttributeList(
    $query: String
    $inCategory: ID
    $inCollection: ID
    $before: String
    $after: String
    $first: Int
    $last: Int
  ) {
    attributes(
      query: $query
      inCategory: $inCategory
      inCollection: $inCollection
      before: $before
      after: $after
      first: $first
      last: $last
    ) {
      edges {
        node {
          ...AttributeFragment
        }
      }
      pageInfo {
        ...PageInfoFragment
      }
    }
  }
`;
export const AttributeListQuery = TypedQuery<
  AttributeList,
  AttributeListVariables
>(attributeList);
