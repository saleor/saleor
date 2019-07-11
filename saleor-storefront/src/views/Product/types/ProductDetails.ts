/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ProductDetails
// ====================================================

export interface ProductDetails_product_thumbnail {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
  /**
   * Alt text for an image.
   */
  alt: string | null;
}

export interface ProductDetails_product_thumbnail2x {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface ProductDetails_product_category_products_edges_node_thumbnail {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
  /**
   * Alt text for an image.
   */
  alt: string | null;
}

export interface ProductDetails_product_category_products_edges_node_thumbnail2x {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface ProductDetails_product_category_products_edges_node_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface ProductDetails_product_category_products_edges_node_price {
  __typename: "Money";
  /**
   * Amount of money.
   */
  amount: number;
  /**
   * Currency code.
   */
  currency: string;
  /**
   * Money formatted according to the current locale.
   */
  localized: string;
}

export interface ProductDetails_product_category_products_edges_node {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * The main thumbnail for a product.
   */
  thumbnail: ProductDetails_product_category_products_edges_node_thumbnail | null;
  /**
   * The main thumbnail for a product.
   */
  thumbnail2x: ProductDetails_product_category_products_edges_node_thumbnail2x | null;
  category: ProductDetails_product_category_products_edges_node_category;
  /**
   * The product's default base price.
   */
  price: ProductDetails_product_category_products_edges_node_price | null;
}

export interface ProductDetails_product_category_products_edges {
  __typename: "ProductCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: ProductDetails_product_category_products_edges_node;
}

export interface ProductDetails_product_category_products {
  __typename: "ProductCountableConnection";
  edges: ProductDetails_product_category_products_edges[];
}

export interface ProductDetails_product_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * List of products in the category.
   */
  products: ProductDetails_product_category_products | null;
}

export interface ProductDetails_product_price {
  __typename: "Money";
  /**
   * Amount of money.
   */
  amount: number;
  /**
   * Currency code.
   */
  currency: string;
  /**
   * Money formatted according to the current locale.
   */
  localized: string;
}

export interface ProductDetails_product_images {
  __typename: "ProductImage";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * The URL of the image.
   */
  url: string;
}

export interface ProductDetails_product_variants_price {
  __typename: "Money";
  /**
   * Currency code.
   */
  currency: string;
  /**
   * Amount of money.
   */
  amount: number;
  /**
   * Money formatted according to the current locale.
   */
  localized: string;
}

export interface ProductDetails_product_variants_attributes_attribute {
  __typename: "Attribute";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * Name of an attribute displayed in the interface.
   */
  name: string | null;
}

export interface ProductDetails_product_variants_attributes_value {
  __typename: "AttributeValue";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * Name of a value displayed in the interface.
   */
  name: string | null;
  /**
   * Name of a value displayed in the interface.
   */
  value: string | null;
}

export interface ProductDetails_product_variants_attributes {
  __typename: "SelectedAttribute";
  /**
   * Name of an attribute displayed in the interface.
   */
  attribute: ProductDetails_product_variants_attributes_attribute;
  /**
   * Value of an attribute.
   */
  value: ProductDetails_product_variants_attributes_value;
}

export interface ProductDetails_product_variants {
  __typename: "ProductVariant";
  /**
   * The ID of the object.
   */
  id: string;
  sku: string;
  name: string;
  /**
   * Quantity of a product available for sale.
   */
  stockQuantity: number;
  /**
   * Whether the variant is in stock and visible or not.
   */
  isAvailable: boolean | null;
  /**
   * Price of the product variant.
   */
  price: ProductDetails_product_variants_price | null;
  /**
   * List of attributes assigned to this variant.
   */
  attributes: ProductDetails_product_variants_attributes[];
}

export interface ProductDetails_product_availability {
  __typename: "ProductPricingInfo";
  /**
   * Whether it is in stock and visible or not.
   */
  available: boolean | null;
}

export interface ProductDetails_product {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * The main thumbnail for a product.
   */
  thumbnail: ProductDetails_product_thumbnail | null;
  /**
   * The main thumbnail for a product.
   */
  thumbnail2x: ProductDetails_product_thumbnail2x | null;
  descriptionJson: any;
  category: ProductDetails_product_category;
  /**
   * The product's default base price.
   */
  price: ProductDetails_product_price | null;
  /**
   * List of images for the product
   */
  images: (ProductDetails_product_images | null)[] | null;
  /**
   * List of variants for the product
   */
  variants: (ProductDetails_product_variants | null)[] | null;
  seoDescription: string | null;
  seoTitle: string | null;
  /**
   * Informs about product's availability in the
   *                storefront, current price and discounts.
   */
  availability: ProductDetails_product_availability | null;
}

export interface ProductDetails {
  /**
   * Lookup a product by ID.
   */
  product: ProductDetails_product | null;
}

export interface ProductDetailsVariables {
  id: string;
}
