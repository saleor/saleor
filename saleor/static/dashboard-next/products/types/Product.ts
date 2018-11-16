/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: Product
// ====================================================

export interface Product_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface Product_collections_edges_node {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface Product_collections_edges {
  __typename: "CollectionCountableEdge";
  node: Product_collections_edges_node;
}

export interface Product_collections {
  __typename: "CollectionCountableConnection";
  edges: Product_collections_edges[];
}

export interface Product_price {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface Product_margin {
  __typename: "Margin";
  start: number | null;
  stop: number | null;
}

export interface Product_purchaseCost_start {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface Product_purchaseCost_stop {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface Product_purchaseCost {
  __typename: "MoneyRange";
  start: Product_purchaseCost_start | null;
  stop: Product_purchaseCost_stop | null;
}

export interface Product_attributes_attribute_values {
  __typename: "AttributeValue";
  name: string | null;
  slug: string | null;
}

export interface Product_attributes_attribute {
  __typename: "Attribute";
  id: string;
  slug: string | null;
  name: string | null;
  values: (Product_attributes_attribute_values | null)[] | null;
}

export interface Product_attributes_value {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface Product_attributes {
  __typename: "SelectedAttribute";
  attribute: Product_attributes_attribute;
  value: Product_attributes_value;
}

export interface Product_availability_priceRange_start_net {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface Product_availability_priceRange_start {
  __typename: "TaxedMoney";
  net: Product_availability_priceRange_start_net;
}

export interface Product_availability_priceRange_stop_net {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface Product_availability_priceRange_stop {
  __typename: "TaxedMoney";
  net: Product_availability_priceRange_stop_net;
}

export interface Product_availability_priceRange {
  __typename: "TaxedMoneyRange";
  start: Product_availability_priceRange_start | null;
  stop: Product_availability_priceRange_stop | null;
}

export interface Product_availability {
  __typename: "ProductAvailability";
  available: boolean | null;
  priceRange: Product_availability_priceRange | null;
}

export interface Product_images_edges_node {
  __typename: "ProductImage";
  id: string;
  alt: string;
  sortOrder: number;
  url: string;
}

export interface Product_images_edges {
  __typename: "ProductImageCountableEdge";
  node: Product_images_edges_node;
}

export interface Product_images {
  __typename: "ProductImageCountableConnection";
  edges: Product_images_edges[];
}

export interface Product_variants_edges_node_priceOverride {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface Product_variants_edges_node {
  __typename: "ProductVariant";
  id: string;
  sku: string;
  name: string;
  priceOverride: Product_variants_edges_node_priceOverride | null;
  stockQuantity: number;
  margin: number | null;
}

export interface Product_variants_edges {
  __typename: "ProductVariantCountableEdge";
  node: Product_variants_edges_node;
}

export interface Product_variants {
  __typename: "ProductVariantCountableConnection";
  edges: Product_variants_edges[];
}

export interface Product_productType {
  __typename: "ProductType";
  id: string;
  name: string;
  hasVariants: boolean;
}

export interface Product {
  __typename: "Product";
  id: string;
  name: string;
  description: string;
  seoTitle: string | null;
  seoDescription: string | null;
  category: Product_category;
  collections: Product_collections | null;
  price: Product_price | null;
  margin: Product_margin | null;
  purchaseCost: Product_purchaseCost | null;
  isPublished: boolean;
  chargeTaxes: boolean;
  availableOn: any | null;
  attributes: Product_attributes[];
  availability: Product_availability | null;
  images: Product_images | null;
  variants: Product_variants | null;
  productType: Product_productType;
  url: string;
}
