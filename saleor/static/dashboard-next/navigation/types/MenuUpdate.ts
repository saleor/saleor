/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { MenuItemMoveInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: MenuUpdate
// ====================================================

export interface MenuUpdate_menuUpdate_errors {
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

export interface MenuUpdate_menuUpdate {
  __typename: "MenuUpdate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: MenuUpdate_menuUpdate_errors[] | null;
}

export interface MenuUpdate_menuItemMove_errors {
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

export interface MenuUpdate_menuItemMove {
  __typename: "MenuItemMove";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: MenuUpdate_menuItemMove_errors[] | null;
}

export interface MenuUpdate_menuItemBulkDelete_errors {
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

export interface MenuUpdate_menuItemBulkDelete {
  __typename: "MenuItemBulkDelete";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: MenuUpdate_menuItemBulkDelete_errors[] | null;
}

export interface MenuUpdate {
  /**
   * Updates a menu.
   */
  menuUpdate: MenuUpdate_menuUpdate | null;
  /**
   * Moves items of menus
   */
  menuItemMove: MenuUpdate_menuItemMove | null;
  /**
   * Deletes menu items.
   */
  menuItemBulkDelete: MenuUpdate_menuItemBulkDelete | null;
}

export interface MenuUpdateVariables {
  id: string;
  name: string;
  moves: (MenuItemMoveInput | null)[];
  removeIds: (string | null)[];
}
