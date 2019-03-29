import gql from "graphql-tag";

import { TypedMutation } from "../mutations";
import {
  categoryTranslationFragment,
  collectionTranslationFragment,
  productTranslationFragment
} from "./queries";
import {
  UpdateCategoryTranslations,
  UpdateCategoryTranslationsVariables
} from "./types/UpdateCategoryTranslations";
import {
  UpdateCollectionTranslations,
  UpdateCollectionTranslationsVariables
} from "./types/UpdateCollectionTranslations";
import {
  UpdateProductTranslations,
  UpdateProductTranslationsVariables
} from "./types/UpdateProductTranslations";

const updateProductTranslations = gql`
  ${productTranslationFragment}
  mutation UpdateProductTranslations(
    $id: ID!
    $input: TranslationInput!
    $language: LanguageCodeEnum!
  ) {
    productTranslate(id: $id, input: $input, languageCode: $language) {
      errors {
        field
        message
      }
      product {
        ...ProductTranslationFragment
      }
    }
  }
`;
export const TypedUpdateProductTranslations = TypedMutation<
  UpdateProductTranslations,
  UpdateProductTranslationsVariables
>(updateProductTranslations);

const updateCategoryTranslations = gql`
  ${categoryTranslationFragment}
  mutation UpdateCategoryTranslations(
    $id: ID!
    $input: TranslationInput!
    $language: LanguageCodeEnum!
  ) {
    categoryTranslate(id: $id, input: $input, languageCode: $language) {
      errors {
        field
        message
      }
      category {
        ...CategoryTranslationFragment
      }
    }
  }
`;
export const TypedUpdateCategoryTranslations = TypedMutation<
  UpdateCategoryTranslations,
  UpdateCategoryTranslationsVariables
>(updateCategoryTranslations);

const updateCollectionTranslations = gql`
  ${collectionTranslationFragment}
  mutation UpdateCollectionTranslations(
    $id: ID!
    $input: TranslationInput!
    $language: LanguageCodeEnum!
  ) {
    collectionTranslate(id: $id, input: $input, languageCode: $language) {
      errors {
        field
        message
      }
      collection {
        ...CollectionTranslationFragment
      }
    }
  }
`;
export const TypedUpdateCollectionTranslations = TypedMutation<
  UpdateCollectionTranslations,
  UpdateCollectionTranslationsVariables
>(updateCollectionTranslations);
