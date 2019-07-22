/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { CategoryInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: CategoryUpdate
// ====================================================

export interface CategoryUpdate_categoryUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface CategoryUpdate_categoryUpdate_category_backgroundImage {
  __typename: "Image";
  alt: string | null;
  url: string;
}

export interface CategoryUpdate_categoryUpdate_category_parent {
  __typename: "Category";
  id: string;
}

export interface CategoryUpdate_categoryUpdate_category {
  __typename: "Category";
  id: string;
  backgroundImage: CategoryUpdate_categoryUpdate_category_backgroundImage | null;
  name: string;
  descriptionJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  parent: CategoryUpdate_categoryUpdate_category_parent | null;
}

export interface CategoryUpdate_categoryUpdate {
  __typename: "CategoryUpdate";
  errors: CategoryUpdate_categoryUpdate_errors[] | null;
  category: CategoryUpdate_categoryUpdate_category | null;
}

export interface CategoryUpdate {
  categoryUpdate: CategoryUpdate_categoryUpdate | null;
}

export interface CategoryUpdateVariables {
  id: string;
  input: CategoryInput;
}
