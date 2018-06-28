import gql from "graphql-tag";
import { Mutation, MutationProps } from "react-apollo";

import {
  ProductDeleteMutation,
  ProductDeleteMutationVariables,
  ProductImageCreateMutation,
  ProductImageCreateMutationVariables,
  ProductImageReorderMutation,
  ProductImageReorderMutationVariables,
} from "../gql-types";

import { fragmentProductImage } from "./queries";

export const TypedProductImageCreateMutation = Mutation as React.ComponentType<
  MutationProps<ProductImageCreateMutation, ProductImageCreateMutationVariables>
>;

export const productImageCreateMutation = gql`
  mutation ProductImageCreate($product: ID!, $image: Upload!, $alt: String) {
    productImageCreate(input: { alt: $alt, image: $image, product: $product }) {
      errors {
        field
        message
      }
      productImage {
        id
        sortOrder
        image
        alt
        url
      }
    }
  }
`;

export const TypedProductDeleteMutation = Mutation as React.ComponentType<
  MutationProps<ProductDeleteMutation, ProductDeleteMutationVariables>
>;

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

export const TypedProductImagesReorder = Mutation as React.ComponentType<
  MutationProps<
    ProductImageReorderMutation,
    ProductImageReorderMutationVariables
  >
>;

export const productImagesReorder = gql`
  ${fragmentProductImage}
  mutation ProductImageReorder($productId: ID!, $imagesIds: [ID]!) {
    productImageReorder(productId: $productId, imagesIds: $imagesIds) {
      errors {
        field
        message
      }
      productImages {
        ...ProductImage
      }
    }
  }
`;
