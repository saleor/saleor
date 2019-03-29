import gql from "graphql-tag";

import { pageInfoFragment, TypedQuery } from "../queries";
import {
  CategoryTranslationDetails,
  CategoryTranslationDetailsVariables
} from "./types/CategoryTranslationDetails";
import {
  CategoryTranslations,
  CategoryTranslationsVariables
} from "./types/CategoryTranslations";
import {
  CollectionTranslationDetails,
  CollectionTranslationDetailsVariables
} from "./types/CollectionTranslationDetails";
import {
  CollectionTranslations,
  CollectionTranslationsVariables
} from "./types/CollectionTranslations";
import {
  ProductTranslationDetails,
  ProductTranslationDetailsVariables
} from "./types/ProductTranslationDetails";
import {
  ProductTranslations,
  ProductTranslationsVariables
} from "./types/ProductTranslations";

export const categoryTranslationFragment = gql`
  fragment CategoryTranslationFragment on Category {
    id
    name
    descriptionJson
    seoDescription
    seoTitle
    translation(languageCode: $language) {
      id
      descriptionJson
      language {
        language
      }
      name
      seoDescription
      seoTitle
    }
  }
`;
export const collectionTranslationFragment = gql`
  fragment CollectionTranslationFragment on Collection {
    id
    name
    descriptionJson
    seoDescription
    seoTitle
    translation(languageCode: $language) {
      id
      descriptionJson
      language {
        language
      }
      name
      seoDescription
      seoTitle
    }
  }
`;
export const productTranslationFragment = gql`
  fragment ProductTranslationFragment on Product {
    id
    name
    descriptionJson
    seoDescription
    seoTitle
    translation(languageCode: $language) {
      id
      descriptionJson
      language {
        code
        language
      }
      name
      seoDescription
      seoTitle
    }
  }
`;

const categoryTranslations = gql`
  ${pageInfoFragment}
  ${categoryTranslationFragment}
  query CategoryTranslations(
    $language: LanguageCodeEnum!
    $first: Int
    $after: String
    $last: Int
    $before: String
  ) {
    categories(before: $before, after: $after, first: $first, last: $last) {
      edges {
        node {
          ...CategoryTranslationFragment
        }
      }
      pageInfo {
        ...PageInfoFragment
      }
    }
  }
`;
export const TypedCategoryTranslations = TypedQuery<
  CategoryTranslations,
  CategoryTranslationsVariables
>(categoryTranslations);

const collectionTranslations = gql`
  ${pageInfoFragment}
  ${collectionTranslationFragment}
  query CollectionTranslations(
    $language: LanguageCodeEnum!
    $first: Int
    $after: String
    $last: Int
    $before: String
  ) {
    collections(before: $before, after: $after, first: $first, last: $last) {
      edges {
        node {
          ...CollectionTranslationFragment
        }
      }
      pageInfo {
        ...PageInfoFragment
      }
    }
  }
`;
export const TypedCollectionTranslations = TypedQuery<
  CollectionTranslations,
  CollectionTranslationsVariables
>(collectionTranslations);

const productTranslations = gql`
  ${pageInfoFragment}
  ${productTranslationFragment}
  query ProductTranslations(
    $language: LanguageCodeEnum!
    $first: Int
    $after: String
    $last: Int
    $before: String
  ) {
    products(before: $before, after: $after, first: $first, last: $last) {
      edges {
        node {
          ...ProductTranslationFragment
        }
      }
      pageInfo {
        ...PageInfoFragment
      }
    }
  }
`;
export const TypedProductTranslations = TypedQuery<
  ProductTranslations,
  ProductTranslationsVariables
>(productTranslations);

const productTranslationDetails = gql`
  ${productTranslationFragment}
  query ProductTranslationDetails($id: ID!, $language: LanguageCodeEnum!) {
    product(id: $id) {
      ...ProductTranslationFragment
    }
  }
`;
export const TypedProductTranslationDetails = TypedQuery<
  ProductTranslationDetails,
  ProductTranslationDetailsVariables
>(productTranslationDetails);

const categoryTranslationDetails = gql`
  ${categoryTranslationFragment}
  query CategoryTranslationDetails($id: ID!, $language: LanguageCodeEnum!) {
    category(id: $id) {
      ...CategoryTranslationFragment
    }
  }
`;
export const TypedCategoryTranslationDetails = TypedQuery<
  CategoryTranslationDetails,
  CategoryTranslationDetailsVariables
>(categoryTranslationDetails);

const collectionTranslationDetails = gql`
  ${collectionTranslationFragment}
  query CollectionTranslationDetails($id: ID!, $language: LanguageCodeEnum!) {
    collection(id: $id) {
      ...CollectionTranslationFragment
    }
  }
`;
export const TypedCollectionTranslationDetails = TypedQuery<
  CollectionTranslationDetails,
  CollectionTranslationDetailsVariables
>(collectionTranslationDetails);
