/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: VariantList
// ====================================================

export interface VariantList_productVariants_edges_node_price {
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

export interface VariantList_productVariants_edges_node_attributes_attribute {
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

export interface VariantList_productVariants_edges_node_attributes_value {
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

export interface VariantList_productVariants_edges_node_attributes {
  __typename: "SelectedAttribute";
  /**
   * Name of an attribute displayed in the interface.
   */
  attribute: VariantList_productVariants_edges_node_attributes_attribute;
  /**
   * Value of an attribute.
   */
  value: VariantList_productVariants_edges_node_attributes_value;
}

export interface VariantList_productVariants_edges_node_product_thumbnail {
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

export interface VariantList_productVariants_edges_node_product_thumbnail2x {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface VariantList_productVariants_edges_node_product {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * The main thumbnail for a product.
   */
  thumbnail: VariantList_productVariants_edges_node_product_thumbnail | null;
  /**
   * The main thumbnail for a product.
   */
  thumbnail2x: VariantList_productVariants_edges_node_product_thumbnail2x | null;
}

export interface VariantList_productVariants_edges_node {
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
  price: VariantList_productVariants_edges_node_price | null;
  /**
   * List of attributes assigned to this variant.
   */
  attributes: VariantList_productVariants_edges_node_attributes[];
  product: VariantList_productVariants_edges_node_product;
}

export interface VariantList_productVariants_edges {
  __typename: "ProductVariantCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: VariantList_productVariants_edges_node;
}

export interface VariantList_productVariants {
  __typename: "ProductVariantCountableConnection";
  edges: VariantList_productVariants_edges[];
}

export interface VariantList {
  /**
   * Lookup multiple variants by ID
   */
  productVariants: VariantList_productVariants | null;
}

export interface VariantListVariables {
  ids?: string[] | null;
}
