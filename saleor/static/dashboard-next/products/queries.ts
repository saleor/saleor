import gql from "graphql-tag";

import { TypedQuery } from "../queries";
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

export const fragmentProduct = gql`
  ${fragmentProductImage}
  ${fragmentMoney}
  fragment Product on Product {
    id
    name
    description
    seoTitle
    seoDescription
    category {
      id
      name
    }
    collections {
      edges {
        node {
          id
          name
        }
      }
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
    availableOn
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
      edges {
        node {
          ...ProductImageFragment
        }
      }
    }
    variants {
      edges {
        node {
          id
          sku
          name
          priceOverride {
            ...Money
          }
          stockQuantity
          margin
        }
      }
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
      edges {
        node {
          id
        }
      }
    }
    name
    priceOverride {
      ...Money
    }
    product {
      id
      images {
        edges {
          node {
            ...ProductImageFragment
          }
        }
      }
      name
      thumbnailUrl
      variants {
        totalCount
        edges {
          node {
            id
            name
            sku
            image: images(first: 1) {
              edges {
                node {
                  id
                  url
                }
              }
            }
          }
        }
      }
    }
    sku
    quantity
    quantityAllocated
  }
`;

const productListQuery = gql`
  ${fragmentMoney}
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
          id
          name
          thumbnailUrl
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
  ${fragmentProduct}
  query ProductDetails($id: ID!) {
    product(id: $id) {
      ...Product
    }
    collections {
      edges {
        node {
          id
          name
        }
      }
    }
    categories {
      edges {
        node {
          id
          name
        }
      }
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
    productTypes {
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
    collections {
      edges {
        node {
          id
          name
        }
      }
    }
    categories {
      edges {
        node {
          id
          name
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
        edges {
          node {
            id
            sortOrder
            url
          }
        }
      }
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
      variants {
        edges {
          node {
            id
            name
            sku
            image: images(first: 1) {
              edges {
                node {
                  id
                  url
                }
              }
            }
          }
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
      mainImage: imageById(id: $imageId) {
        id
        alt
        url
      }
      images {
        edges {
          node {
            id
            url(size: 48)
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
  }
`;
export const TypedProductImageQuery = TypedQuery<
  ProductImageById,
  ProductImageByIdVariables
>(productImageQuery);
