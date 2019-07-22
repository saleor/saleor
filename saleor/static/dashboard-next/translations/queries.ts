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
  PageTranslationDetails,
  PageTranslationDetailsVariables
} from "./types/PageTranslationDetails";
import {
  PageTranslations,
  PageTranslationsVariables
} from "./types/PageTranslations";
import {
  ProductTranslationDetails,
  ProductTranslationDetailsVariables
} from "./types/ProductTranslationDetails";
import {
  ProductTranslations,
  ProductTranslationsVariables
} from "./types/ProductTranslations";
import {
  ProductTypeTranslationDetails,
  ProductTypeTranslationDetailsVariables
} from "./types/ProductTypeTranslationDetails";
import {
  ProductTypeTranslations,
  ProductTypeTranslationsVariables
} from "./types/ProductTypeTranslations";
import {
  SaleTranslationDetails,
  SaleTranslationDetailsVariables
} from "./types/SaleTranslationDetails";
import {
  SaleTranslations,
  SaleTranslationsVariables
} from "./types/SaleTranslations";
import {
  VoucherTranslationDetails,
  VoucherTranslationDetailsVariables
} from "./types/VoucherTranslationDetails";
import {
  VoucherTranslations,
  VoucherTranslationsVariables
} from "./types/VoucherTranslations";

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
export const saleTranslationFragment = gql`
  fragment SaleTranslationFragment on Sale {
    id
    name
    translation(languageCode: $language) {
      id
      language {
        code
        language
      }
      name
    }
  }
`;
export const voucherTranslationFragment = gql`
  fragment VoucherTranslationFragment on Voucher {
    id
    name
    translation(languageCode: $language) {
      id
      language {
        code
        language
      }
      name
    }
  }
`;
export const shippingMethodTranslationFragment = gql`
  fragment ShippingMethodTranslationFragment on ShippingMethod {
    id
    name
    translation(languageCode: $language) {
      id
      language {
        code
        language
      }
      name
    }
  }
`;
export const pageTranslationFragment = gql`
  fragment PageTranslationFragment on Page {
    id
    contentJson
    seoDescription
    seoTitle
    title

    translation(languageCode: $language) {
      id
      contentJson
      seoDescription
      seoTitle
      title
      language {
        code
        language
      }
    }
  }
`;
export const productTypeTranslationFragment = gql`
  fragment AttributeTranslationFragment on Attribute {
    id
    name
    translation(languageCode: $language) {
      id
      name
    }
    values {
      id
      name
      translation(languageCode: $language) {
        id
        name
      }
    }
  }
  fragment ProductTypeTranslationFragment on ProductType {
    id
    name
    productAttributes {
      ...AttributeTranslationFragment
    }
    variantAttributes {
      ...AttributeTranslationFragment
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

const pageTranslations = gql`
  ${pageInfoFragment}
  ${pageTranslationFragment}
  query PageTranslations(
    $language: LanguageCodeEnum!
    $first: Int
    $after: String
    $last: Int
    $before: String
  ) {
    pages(before: $before, after: $after, first: $first, last: $last) {
      edges {
        node {
          ...PageTranslationFragment
        }
      }
      pageInfo {
        ...PageInfoFragment
      }
    }
  }
`;
export const TypedPageTranslations = TypedQuery<
  PageTranslations,
  PageTranslationsVariables
>(pageTranslations);

const voucherTranslations = gql`
  ${pageInfoFragment}
  ${voucherTranslationFragment}
  query VoucherTranslations(
    $language: LanguageCodeEnum!
    $first: Int
    $after: String
    $last: Int
    $before: String
  ) {
    vouchers(before: $before, after: $after, first: $first, last: $last) {
      edges {
        node {
          ...VoucherTranslationFragment
        }
      }
      pageInfo {
        ...PageInfoFragment
      }
    }
  }
`;
export const TypedVoucherTranslations = TypedQuery<
  VoucherTranslations,
  VoucherTranslationsVariables
>(voucherTranslations);

const saleTranslations = gql`
  ${pageInfoFragment}
  ${saleTranslationFragment}
  query SaleTranslations(
    $language: LanguageCodeEnum!
    $first: Int
    $after: String
    $last: Int
    $before: String
  ) {
    sales(before: $before, after: $after, first: $first, last: $last) {
      edges {
        node {
          ...SaleTranslationFragment
        }
      }
      pageInfo {
        ...PageInfoFragment
      }
    }
  }
`;
export const TypedSaleTranslations = TypedQuery<
  SaleTranslations,
  SaleTranslationsVariables
>(saleTranslations);

const productTypeTranslations = gql`
  ${pageInfoFragment}
  ${productTypeTranslationFragment}
  query ProductTypeTranslations(
    $language: LanguageCodeEnum!
    $first: Int
    $after: String
    $last: Int
    $before: String
  ) {
    productTypes(before: $before, after: $after, first: $first, last: $last) {
      edges {
        node {
          ...ProductTypeTranslationFragment
        }
      }
      pageInfo {
        ...PageInfoFragment
      }
    }
  }
`;
export const TypedProductTypeTranslations = TypedQuery<
  ProductTypeTranslations,
  ProductTypeTranslationsVariables
>(productTypeTranslations);

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

const pageTranslationDetails = gql`
  ${pageTranslationFragment}
  query PageTranslationDetails($id: ID!, $language: LanguageCodeEnum!) {
    page(id: $id) {
      ...PageTranslationFragment
    }
  }
`;
export const TypedPageTranslationDetails = TypedQuery<
  PageTranslationDetails,
  PageTranslationDetailsVariables
>(pageTranslationDetails);

const saleTranslationDetails = gql`
  ${saleTranslationFragment}
  query SaleTranslationDetails($id: ID!, $language: LanguageCodeEnum!) {
    sale(id: $id) {
      ...SaleTranslationFragment
    }
  }
`;
export const TypedSaleTranslationDetails = TypedQuery<
  SaleTranslationDetails,
  SaleTranslationDetailsVariables
>(saleTranslationDetails);

const voucherTranslationDetails = gql`
  ${voucherTranslationFragment}
  query VoucherTranslationDetails($id: ID!, $language: LanguageCodeEnum!) {
    voucher(id: $id) {
      ...VoucherTranslationFragment
    }
  }
`;
export const TypedVoucherTranslationDetails = TypedQuery<
  VoucherTranslationDetails,
  VoucherTranslationDetailsVariables
>(voucherTranslationDetails);

const productTypeTranslationDetails = gql`
  ${productTypeTranslationFragment}
  query ProductTypeTranslationDetails($id: ID!, $language: LanguageCodeEnum!) {
    productType(id: $id) {
      ...ProductTypeTranslationFragment
    }
  }
`;
export const TypedProductTypeTranslationDetails = TypedQuery<
  ProductTypeTranslationDetails,
  ProductTypeTranslationDetailsVariables
>(productTypeTranslationDetails);
