import gql from "graphql-tag";

import { TypedMutation } from "../mutations";
import { ProductCreate, ProductCreateVariables } from "./types/ProductCreate";
import { ProductDelete, ProductDeleteVariables } from "./types/ProductDelete";
import {
  ProductImageCreate,
  ProductImageCreateVariables
} from "./types/ProductImageCreate";
import {
  ProductImageDelete,
  ProductImageDeleteVariables
} from "./types/ProductImageDelete";
import {
  ProductImageReorder,
  ProductImageReorderVariables
} from "./types/ProductImageReorder";
import {
  ProductImageUpdate,
  ProductImageUpdateVariables
} from "./types/ProductImageUpdate";
import { ProductUpdate, ProductUpdateVariables } from "./types/ProductUpdate";
import {
  SimpleProductUpdate,
  SimpleProductUpdateVariables
} from "./types/SimpleProductUpdate";
import { VariantCreate, VariantCreateVariables } from "./types/VariantCreate";
import { VariantDelete, VariantDeleteVariables } from "./types/VariantDelete";
import {
  VariantImageAssign,
  VariantImageAssignVariables
} from "./types/VariantImageAssign";
import {
  VariantImageUnassign,
  VariantImageUnassignVariables
} from "./types/VariantImageUnassign";
import { VariantUpdate, VariantUpdateVariables } from "./types/VariantUpdate";

import { fragmentVariant, productFragmentDetails } from "./queries";
import {
  productBulkDelete,
  productBulkDeleteVariables
} from "./types/productBulkDelete";
import {
  productBulkPublish,
  productBulkPublishVariables
} from "./types/productBulkPublish";
import {
  ProductVariantBulkDelete,
  ProductVariantBulkDeleteVariables
} from "./types/ProductVariantBulkDelete";

export const productImageCreateMutation = gql`
  ${productFragmentDetails}
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
  ProductImageCreate,
  ProductImageCreateVariables
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
  ProductDelete,
  ProductDeleteVariables
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
          id
          alt
          sortOrder
          url
        }
      }
    }
  }
`;
export const TypedProductImagesReorder = TypedMutation<
  ProductImageReorder,
  ProductImageReorderVariables
>(productImagesReorder);

export const productUpdateMutation = gql`
  ${productFragmentDetails}
  mutation ProductUpdate(
    $id: ID!
    $attributes: [AttributeValueInput]
    $publicationDate: Date
    $category: ID
    $chargeTaxes: Boolean!
    $collections: [ID]
    $descriptionJson: JSONString
    $isPublished: Boolean!
    $name: String
    $price: Decimal
  ) {
    productUpdate(
      id: $id
      input: {
        attributes: $attributes
        publicationDate: $publicationDate
        category: $category
        chargeTaxes: $chargeTaxes
        collections: $collections
        descriptionJson: $descriptionJson
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
  ProductUpdate,
  ProductUpdateVariables
>(productUpdateMutation);

export const simpleProductUpdateMutation = gql`
  ${productFragmentDetails}
  ${fragmentVariant}
  mutation SimpleProductUpdate(
    $id: ID!
    $attributes: [AttributeValueInput]
    $publicationDate: Date
    $category: ID
    $chargeTaxes: Boolean!
    $collections: [ID]
    $descriptionJson: JSONString
    $isPublished: Boolean!
    $name: String
    $price: Decimal
    $productVariantId: ID!
    $productVariantInput: ProductVariantInput!
  ) {
    productUpdate(
      id: $id
      input: {
        attributes: $attributes
        publicationDate: $publicationDate
        category: $category
        chargeTaxes: $chargeTaxes
        collections: $collections
        descriptionJson: $descriptionJson
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
    productVariantUpdate(id: $productVariantId, input: $productVariantInput) {
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
export const TypedSimpleProductUpdateMutation = TypedMutation<
  SimpleProductUpdate,
  SimpleProductUpdateVariables
>(simpleProductUpdateMutation);

export const productCreateMutation = gql`
  ${productFragmentDetails}
  mutation ProductCreate(
    $attributes: [AttributeValueInput]
    $publicationDate: Date
    $category: ID!
    $chargeTaxes: Boolean!
    $collections: [ID]
    $descriptionJson: JSONString
    $isPublished: Boolean!
    $name: String!
    $price: Decimal
    $productType: ID!
    $sku: String
    $stockQuantity: Int
  ) {
    productCreate(
      input: {
        attributes: $attributes
        publicationDate: $publicationDate
        category: $category
        chargeTaxes: $chargeTaxes
        collections: $collections
        descriptionJson: $descriptionJson
        isPublished: $isPublished
        name: $name
        price: $price
        productType: $productType
        sku: $sku
        quantity: $stockQuantity
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
  ProductCreate,
  ProductCreateVariables
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
  VariantDelete,
  VariantDeleteVariables
>(variantDeleteMutation);

export const variantUpdateMutation = gql`
  ${fragmentVariant}
  mutation VariantUpdate(
    $id: ID!
    $attributes: [AttributeValueInput]
    $costPrice: Decimal
    $priceOverride: Decimal
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
  VariantUpdate,
  VariantUpdateVariables
>(variantUpdateMutation);

export const variantCreateMutation = gql`
  ${fragmentVariant}
  mutation VariantCreate(
    $attributes: [AttributeValueInput]!
    $costPrice: Decimal
    $priceOverride: Decimal
    $product: ID!
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
  VariantCreate,
  VariantCreateVariables
>(variantCreateMutation);

export const productImageDeleteMutation = gql`
  mutation ProductImageDelete($id: ID!) {
    productImageDelete(id: $id) {
      product {
        id
        images {
          id
        }
      }
    }
  }
`;
export const TypedProductImageDeleteMutation = TypedMutation<
  ProductImageDelete,
  ProductImageDeleteVariables
>(productImageDeleteMutation);

export const productImageUpdateMutation = gql`
  ${productFragmentDetails}
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
  ProductImageUpdate,
  ProductImageUpdateVariables
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
  VariantImageAssign,
  VariantImageAssignVariables
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
  VariantImageUnassign,
  VariantImageUnassignVariables
>(variantImageUnassignMutation);

export const productBulkDeleteMutation = gql`
  mutation productBulkDelete($ids: [ID!]!) {
    productBulkDelete(ids: $ids) {
      errors {
        field
        message
      }
    }
  }
`;
export const TypedProductBulkDeleteMutation = TypedMutation<
  productBulkDelete,
  productBulkDeleteVariables
>(productBulkDeleteMutation);

export const productBulkPublishMutation = gql`
  mutation productBulkPublish($ids: [ID!]!, $isPublished: Boolean!) {
    productBulkPublish(ids: $ids, isPublished: $isPublished) {
      errors {
        field
        message
      }
    }
  }
`;
export const TypedProductBulkPublishMutation = TypedMutation<
  productBulkPublish,
  productBulkPublishVariables
>(productBulkPublishMutation);

export const ProductVariantBulkDeleteMutation = gql`
  mutation ProductVariantBulkDelete($ids: [ID!]!) {
    productVariantBulkDelete(ids: $ids) {
      errors {
        field
        message
      }
    }
  }
`;
export const TypedProductVariantBulkDeleteMutation = TypedMutation<
  ProductVariantBulkDelete,
  ProductVariantBulkDeleteVariables
>(ProductVariantBulkDeleteMutation);
