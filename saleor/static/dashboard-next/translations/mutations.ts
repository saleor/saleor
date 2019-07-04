import gql from "graphql-tag";

import { TypedMutation } from "../mutations";
import {
  categoryTranslationFragment,
  collectionTranslationFragment,
  pageTranslationFragment,
  productTranslationFragment,
  saleTranslationFragment,
  voucherTranslationFragment
} from "./queries";
import {
  UpdateAttributeTranslations,
  UpdateAttributeTranslationsVariables
} from "./types/UpdateAttributeTranslations";
import {
  UpdateAttributeValueTranslations,
  UpdateAttributeValueTranslationsVariables
} from "./types/UpdateAttributeValueTranslations";
import {
  UpdateCategoryTranslations,
  UpdateCategoryTranslationsVariables
} from "./types/UpdateCategoryTranslations";
import {
  UpdateCollectionTranslations,
  UpdateCollectionTranslationsVariables
} from "./types/UpdateCollectionTranslations";
import {
  UpdatePageTranslations,
  UpdatePageTranslationsVariables
} from "./types/UpdatePageTranslations";
import {
  UpdateProductTranslations,
  UpdateProductTranslationsVariables
} from "./types/UpdateProductTranslations";
import {
  UpdateSaleTranslations,
  UpdateSaleTranslationsVariables
} from "./types/UpdateSaleTranslations";
import {
  UpdateVoucherTranslations,
  UpdateVoucherTranslationsVariables
} from "./types/UpdateVoucherTranslations";

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

const updatePageTranslations = gql`
  ${pageTranslationFragment}
  mutation UpdatePageTranslations(
    $id: ID!
    $input: PageTranslationInput!
    $language: LanguageCodeEnum!
  ) {
    pageTranslate(id: $id, input: $input, languageCode: $language) {
      errors {
        field
        message
      }
      page {
        ...PageTranslationFragment
      }
    }
  }
`;
export const TypedUpdatePageTranslations = TypedMutation<
  UpdatePageTranslations,
  UpdatePageTranslationsVariables
>(updatePageTranslations);

const updateVoucherTranslations = gql`
  ${voucherTranslationFragment}
  mutation UpdateVoucherTranslations(
    $id: ID!
    $input: NameTranslationInput!
    $language: LanguageCodeEnum!
  ) {
    voucherTranslate(id: $id, input: $input, languageCode: $language) {
      errors {
        field
        message
      }
      voucher {
        ...VoucherTranslationFragment
      }
    }
  }
`;
export const TypedUpdateVoucherTranslations = TypedMutation<
  UpdateVoucherTranslations,
  UpdateVoucherTranslationsVariables
>(updateVoucherTranslations);

const updateSaleTranslations = gql`
  ${saleTranslationFragment}
  mutation UpdateSaleTranslations(
    $id: ID!
    $input: NameTranslationInput!
    $language: LanguageCodeEnum!
  ) {
    saleTranslate(id: $id, input: $input, languageCode: $language) {
      errors {
        field
        message
      }
      sale {
        ...SaleTranslationFragment
      }
    }
  }
`;
export const TypedUpdateSaleTranslations = TypedMutation<
  UpdateSaleTranslations,
  UpdateSaleTranslationsVariables
>(updateSaleTranslations);

const updateAttributeTranslations = gql`
  mutation UpdateAttributeTranslations(
    $id: ID!
    $input: NameTranslationInput!
    $language: LanguageCodeEnum!
  ) {
    attributeTranslate(id: $id, input: $input, languageCode: $language) {
      errors {
        field
        message
      }
      attribute {
        id
        name
        translation(languageCode: $language) {
          id
          name
        }
      }
    }
  }
`;
export const TypedUpdateAttributeTranslations = TypedMutation<
  UpdateAttributeTranslations,
  UpdateAttributeTranslationsVariables
>(updateAttributeTranslations);

const updateAttributeValueTranslations = gql`
  mutation UpdateAttributeValueTranslations(
    $id: ID!
    $input: NameTranslationInput!
    $language: LanguageCodeEnum!
  ) {
    attributeValueTranslate(id: $id, input: $input, languageCode: $language) {
      errors {
        field
        message
      }
      attributeValue {
        id
        name
        translation(languageCode: $language) {
          id
          name
        }
      }
    }
  }
`;
export const TypedUpdateAttributeValueTranslations = TypedMutation<
  UpdateAttributeValueTranslations,
  UpdateAttributeValueTranslationsVariables
>(updateAttributeValueTranslations);
