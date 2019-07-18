/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { MenuItemInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: MenuItemUpdate
// ====================================================

export interface MenuItemUpdate_menuItemUpdate_errors {
  __typename: "Error";
  /**
   * Name of a field that caused the error. A value of
   *         `null` indicates that the error isn't associated with a particular
   *         field.
   */
  field: string | null;
  /**
   * The error message.
   */
  message: string | null;
}

export interface MenuItemUpdate_menuItemUpdate_menuItem_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuItemUpdate_menuItem_collection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuItemUpdate_menuItem_page {
  __typename: "Page";
  /**
   * The ID of the object.
   */
  id: string;
  title: string;
}

export interface MenuItemUpdate_menuItemUpdate_menuItem {
  __typename: "MenuItem";
  category: MenuItemUpdate_menuItemUpdate_menuItem_category | null;
  collection: MenuItemUpdate_menuItemUpdate_menuItem_collection | null;
  /**
   * The ID of the object.
   */
  id: string;
  level: number;
  name: string;
  page: MenuItemUpdate_menuItemUpdate_menuItem_page | null;
  sortOrder: number | null;
  /**
   * URL to the menu item.
   */
  url: string | null;
}

export interface MenuItemUpdate_menuItemUpdate {
  __typename: "MenuItemUpdate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: MenuItemUpdate_menuItemUpdate_errors[] | null;
  menuItem: MenuItemUpdate_menuItemUpdate_menuItem | null;
}

export interface MenuItemUpdate {
  /**
   * Updates a menu item.
   */
  menuItemUpdate: MenuItemUpdate_menuItemUpdate | null;
}

export interface MenuItemUpdateVariables {
  id: string;
  input: MenuItemInput;
}
