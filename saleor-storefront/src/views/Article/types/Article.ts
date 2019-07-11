/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: Article
// ====================================================

export interface Article_page {
  __typename: "Page";
  content: string;
  /**
   * The ID of the object.
   */
  id: string;
  seoDescription: string | null;
  seoTitle: string | null;
  slug: string;
  title: string;
}

export interface Article_shop_homepageCollection_backgroundImage {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface Article_shop_homepageCollection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  backgroundImage: Article_shop_homepageCollection_backgroundImage | null;
}

export interface Article_shop {
  __typename: "Shop";
  /**
   * Collection displayed on homepage
   */
  homepageCollection: Article_shop_homepageCollection | null;
}

export interface Article {
  /**
   * Lookup a page by ID or by slug.
   */
  page: Article_page | null;
  /**
   * Represents a shop resources.
   */
  shop: Article_shop | null;
}

export interface ArticleVariables {
  slug: string;
}
