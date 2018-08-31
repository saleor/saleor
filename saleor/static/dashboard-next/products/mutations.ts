import gql from "graphql-tag";

import {
  ProductCreateMutation,
  ProductCreateMutationVariables,
  ProductDeleteMutation,
  ProductDeleteMutationVariables,
  ProductImageCreateMutation,
  ProductImageCreateMutationVariables,
  ProductImageDeleteMutation,
  ProductImageDeleteMutationVariables,
  ProductImageReorderMutation,
  ProductImageReorderMutationVariables,
  ProductImageUpdateMutation,
  ProductImageUpdateMutationVariables,
  ProductUpdateMutation,
  ProductUpdateMutationVariables,
  VariantCreateMutation,
  VariantCreateMutationVariables,
  VariantDeleteMutation,
  VariantDeleteMutationVariables,
  VariantImageAssignMutation,
  VariantImageAssignMutationVariables,
  VariantImageUnassignMutation,
  VariantImageUnassignMutationVariables,
  VariantUpdateMutation,
  VariantUpdateMutationVariables
} from "../gql-types";
import { TypedMutation } from "../mutations";

import { fragmentProduct, fragmentVariant } from "./queries";

export const productImageCreateMutation = gql`
  ${fragmentProduct}
  mutation ProductImageCreate($product: ID!, $image: Upload!, $alt: String) {
    productImageCreate(input: { alt: $alt, image: $image, product: $product }) {
      errors {
        field
        message
      }
      product {
        ...Product
      }
    }
  }
`;
export const TypedProductImageCreateMutation = TypedMutation<
  ProductImageCreateMutation,
  ProductImageCreateMutationVariables
>(productImageCreateMutation);

export const productDeleteMutation = gql`
  mutation ProductDelete($id: ID!) {
    productDelete(id: $id) {
      errors {
        field
        message
      }
      product {
        id
      }
    }
  }
`;
export const TypedProductDeleteMutation = TypedMutation<
  ProductDeleteMutation,
  ProductDeleteMutationVariables
>(productDeleteMutation);

export const productImagesReorder = gql`
  mutation ProductImageReorder($productId: ID!, $imagesIds: [ID]!) {
    productImageReorder(productId: $productId, imagesIds: $imagesIds) {
      errors {
        field
        message
      }
      product {
        id
        images {
          edges {
            node {
              id
              alt
              sortOrder
              url
            }
          }
        }
      }
    }
  }
`;
export const TypedProductImagesReorder = TypedMutation<
  ProductImageReorderMutation,
  ProductImageReorderMutationVariables
>(productImagesReorder);

export const productUpdateMutation = gql`
  ${fragmentProduct}
  mutation ProductUpdate(
    $id: ID!
    $attributes: [AttributeValueInput]
    $availableOn: Date
    $category: ID
    $chargeTaxes: Boolean!
    $collections: [ID]
    $description: String
    $isPublished: Boolean!
    $name: String
    $price: Decimal
  ) {
    productUpdate(
      id: $id
      input: {
        attributes: $attributes
        availableOn: $availableOn
        category: $category
        chargeTaxes: $chargeTaxes
        collections: $collections
        description: $description
        isPublished: $isPublished
        name: $name
        price: $price
      }
    ) {
      errors {
        field
        message
      }
      product {
        ...Product
      }
    }
  }
`;
export const TypedProductUpdateMutation = TypedMutation<
  ProductUpdateMutation,
  ProductUpdateMutationVariables
>(productUpdateMutation);

export const productCreateMutation = gql`
  ${fragmentProduct}
  mutation ProductCreate(
    $attributes: [AttributeValueInput]
    $availableOn: Date
    $category: ID!
    $chargeTaxes: Boolean!
    $collections: [ID]
    $description: String
    $isPublished: Boolean!
    $name: String!
    $price: Decimal
    $productType: ID!
  ) {
    productCreate(
      input: {
        attributes: $attributes
        availableOn: $availableOn
        category: $category
        chargeTaxes: $chargeTaxes
        collections: $collections
        description: $description
        isPublished: $isPublished
        name: $name
        price: $price
        productType: $productType
      }
    ) {
      errors {
        field
        message
      }
      product {
        ...Product
      }
    }
  }
`;
export const TypedProductCreateMutation = TypedMutation<
  ProductCreateMutation,
  ProductCreateMutationVariables
>(productCreateMutation);

export const variantDeleteMutation = gql`
  mutation VariantDelete($id: ID!) {
    productVariantDelete(id: $id) {
      errors {
        field
        message
      }
      productVariant {
        id
      }
    }
  }
`;
export const TypedVariantDeleteMutation = TypedMutation<
  VariantDeleteMutation,
  VariantDeleteMutationVariables
>(variantDeleteMutation);

export const variantUpdateMutation = gql`
  ${fragmentVariant}
  mutation VariantUpdate(
    $id: ID!
    $attributes: [AttributeValueInput]
    $costPrice: Decimal
    $priceOverride: Decimal
    $product: ID
    $sku: String
    $quantity: Int
    $trackInventory: Boolean!
  ) {
    productVariantUpdate(
      id: $id
      input: {
        attributes: $attributes
        costPrice: $costPrice
        priceOverride: $priceOverride
        product: $product
        sku: $sku
        quantity: $quantity
        trackInventory: $trackInventory
      }
    ) {
      errors {
        field
        message
      }
      productVariant {
        ...ProductVariant
      }
    }
  }
`;
export const TypedVariantUpdateMutation = TypedMutation<
  VariantUpdateMutation,
  VariantUpdateMutationVariables
>(variantUpdateMutation);

export const variantCreateMutation = gql`
  ${fragmentVariant}
  mutation VariantCreate(
    $attributes: [AttributeValueInput]
    $costPrice: Decimal
    $priceOverride: Decimal
    $product: ID
    $sku: String
    $quantity: Int
    $trackInventory: Boolean!
  ) {
    productVariantCreate(
      input: {
        attributes: $attributes
        costPrice: $costPrice
        priceOverride: $priceOverride
        product: $product
        sku: $sku
        quantity: $quantity
        trackInventory: $trackInventory
      }
    ) {
      errors {
        field
        message
      }
      productVariant {
        ...ProductVariant
      }
    }
  }
`;
export const TypedVariantCreateMutation = TypedMutation<
  VariantCreateMutation,
  VariantCreateMutationVariables
>(variantCreateMutation);

export const productImageDeleteMutation = gql`
  mutation ProductImageDelete($id: ID!) {
    productImageDelete(id: $id) {
      product {
        id
        images {
          edges {
            node {
              id
            }
          }
        }
      }
    }
  }
`;
export const TypedProductImageDeleteMutation = TypedMutation<
  ProductImageDeleteMutation,
  ProductImageDeleteMutationVariables
>(productImageDeleteMutation);

export const productImageUpdateMutation = gql`
  ${fragmentProduct}
  mutation ProductImageUpdate($id: ID!, $alt: String!) {
    productImageUpdate(id: $id, input: { alt: $alt }) {
      errors {
        field
        message
      }
      product {
        ...Product
      }
    }
  }
`;
export const TypedProductImageUpdateMutation = TypedMutation<
  ProductImageUpdateMutation,
  ProductImageUpdateMutationVariables
>(productImageUpdateMutation);

export const variantImageAssignMutation = gql`
  ${fragmentVariant}
  mutation VariantImageAssign($variantId: ID!, $imageId: ID!) {
    variantImageAssign(variantId: $variantId, imageId: $imageId) {
      errors {
        field
        message
      }
      productVariant {
        ...ProductVariant
      }
    }
  }
`;
export const TypedVariantImageAssignMutation = TypedMutation<
  VariantImageAssignMutation,
  VariantImageAssignMutationVariables
>(variantImageAssignMutation);

export const variantImageUnassignMutation = gql`
  ${fragmentVariant}
  mutation VariantImageUnassign($variantId: ID!, $imageId: ID!) {
    variantImageUnassign(variantId: $variantId, imageId: $imageId) {
      errors {
        field
        message
      }
      productVariant {
        ...ProductVariant
      }
    }
  }
`;
export const TypedVariantImageUnassignMutation = TypedMutation<
  VariantImageUnassignMutation,
  VariantImageUnassignMutationVariables
>(variantImageUnassignMutation);
