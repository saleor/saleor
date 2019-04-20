import gql from "graphql-tag";

import { TypedQuery } from "../queries";
import {
  CategorySearch,
  CategorySearchVariables
} from "./types/CategorySearch";
import {
  CollectionSearch,
  CollectionSearchVariables
} from "./types/CollectionSearch";
import { ProductCreateData } from "./types/ProductCreateData";
import {
  ProductDetails,
  ProductDetailsVariables
} from "./types/ProductDetails";
import {
  ProductImageById,
  ProductImageByIdVariables
} from "./types/ProductImageById";
import { ProductList, ProductListVariables } from "./types/ProductList";
import {
  ProductVariantCreateData,
  ProductVariantCreateDataVariables
} from "./types/ProductVariantCreateData";
import {
  ProductVariantDetails,
  ProductVariantDetailsVariables
} from "./types/ProductVariantDetails";

export const fragmentMoney = gql`
  fragment Money on Money {
    amount
    currency
  }
`;

export const fragmentProductImage = gql`
  fragment ProductImageFragment on ProductImage {
    id
    alt
    sortOrder
    url
  }
`;

export const productFragment = gql`
  ${fragmentMoney}
  fragment ProductFragment on Product {
    id
    name
    thumbnail {
      url
    }
    availability {
      available
    }
    price {
      ...Money
    }
    productType {
      id
      name
    }
  }
`;
export const productFragmentDetails = gql`
  ${fragmentProductImage}
  ${fragmentMoney}
  fragment Product on Product {
    id
    name
    descriptionJson
    seoTitle
    seoDescription
    category {
      id
      name
    }
    collections {
      id
      name
    }
    price {
      ...Money
    }
    margin {
      start
      stop
    }
    purchaseCost {
      start {
        ...Money
      }
      stop {
        ...Money
      }
    }
    isPublished
    chargeTaxes
    publicationDate
    attributes {
      attribute {
        id
        slug
        name
        values {
          name
          slug
        }
      }
      value {
        id
        name
        slug
      }
    }
    availability {
      available
      priceRange {
        start {
          net {
            ...Money
          }
        }
        stop {
          net {
            ...Money
          }
        }
      }
    }
    images {
      ...ProductImageFragment
    }
    variants {
      id
      sku
      name
      priceOverride {
        ...Money
      }
      margin
      quantity
      quantityAllocated
      stockQuantity
    }
    productType {
      id
      name
      hasVariants
    }
    url
  }
`;

export const fragmentVariant = gql`
  ${fragmentMoney}
  ${fragmentProductImage}
  fragment ProductVariant on ProductVariant {
    id
    attributes {
      attribute {
        id
        name
        slug
        values {
          id
          name
          slug
        }
      }
      value {
        id
        name
        slug
      }
    }
    costPrice {
      ...Money
    }
    images {
      id
      url
    }
    name
    priceOverride {
      ...Money
    }
    product {
      id
      images {
        ...ProductImageFragment
      }
      name
      thumbnail {
        url
      }
      variants {
        id
        name
        sku
        images {
          id
          url
        }
      }
    }
    sku
    quantity
    quantityAllocated
  }
`;

const productListQuery = gql`
  ${productFragment}
  query ProductList(
    $first: Int
    $after: String
    $last: Int
    $before: String
    $stockAvailability: StockAvailability
  ) {
    products(
      before: $before
      after: $after
      first: $first
      last: $last
      stockAvailability: $stockAvailability
    ) {
      edges {
        node {
          ...ProductFragment
        }
      }
      pageInfo {
        hasPreviousPage
        hasNextPage
        startCursor
        endCursor
      }
    }
  }
`;
export const TypedProductListQuery = TypedQuery<
  ProductList,
  ProductListVariables
>(productListQuery);

const productDetailsQuery = gql`
  ${productFragmentDetails}
  query ProductDetails($id: ID!) {
    product(id: $id) {
      ...Product
    }
  }
`;
export const TypedProductDetailsQuery = TypedQuery<
  ProductDetails,
  ProductDetailsVariables
>(productDetailsQuery);

const productVariantQuery = gql`
  ${fragmentVariant}
  query ProductVariantDetails($id: ID!) {
    productVariant(id: $id) {
      ...ProductVariant
    }
  }
`;
export const TypedProductVariantQuery = TypedQuery<
  ProductVariantDetails,
  ProductVariantDetailsVariables
>(productVariantQuery);

const productCreateQuery = gql`
  query ProductCreateData {
    productTypes(first: 20) {
      edges {
        node {
          id
          name
          hasVariants
          productAttributes {
            id
            slug
            name
            values {
              id
              sortOrder
              name
              slug
            }
          }
        }
      }
    }
  }
`;
export const TypedProductCreateQuery = TypedQuery<ProductCreateData, {}>(
  productCreateQuery
);

const productVariantCreateQuery = gql`
  query ProductVariantCreateData($id: ID!) {
    product(id: $id) {
      id
      images {
        id
        sortOrder
        url
      }
      name
      productType {
        id
        variantAttributes {
          id
          slug
          name
          values {
            id
            sortOrder
            name
            slug
          }
        }
      }
      thumbnail {
        url
      }
      variants {
        id
        name
        sku
        images {
          id
          url
        }
      }
    }
  }
`;
export const TypedProductVariantCreateQuery = TypedQuery<
  ProductVariantCreateData,
  ProductVariantCreateDataVariables
>(productVariantCreateQuery);

const productImageQuery = gql`
  query ProductImageById($productId: ID!, $imageId: ID!) {
    product(id: $productId) {
      id
      name
      mainImage: imageById(id: $imageId) {
        id
        alt
        url
      }
      images {
        id
        url(size: 48)
      }
    }
  }
`;
export const TypedProductImageQuery = TypedQuery<
  ProductImageById,
  ProductImageByIdVariables
>(productImageQuery);

const categorySearch = gql`
  query CategorySearch($query: String) {
    categories(first: 5, query: $query) {
      edges {
        node {
          id
          name
        }
      }
    }
  }
`;
export const TypedCategorySearchQuery = TypedQuery<
  CategorySearch,
  CategorySearchVariables
>(categorySearch);

const collectionSearch = gql`
  query CollectionSearch($query: String) {
    collections(first: 5, query: $query) {
      edges {
        node {
          id
          name
        }
      }
    }
  }
`;
export const TypedCollectionSearchQuery = TypedQuery<
  CollectionSearch,
  CollectionSearchVariables
>(collectionSearch);
