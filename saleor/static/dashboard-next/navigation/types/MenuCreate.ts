/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { MenuCreateInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: MenuCreate
// ====================================================

export interface MenuCreate_menuCreate_errors {
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

export interface MenuCreate_menuCreate_menu {
  __typename: "Menu";
  /**
   * The ID of the object.
   */
  id: string;
}

export interface MenuCreate_menuCreate {
  __typename: "MenuCreate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: MenuCreate_menuCreate_errors[] | null;
  menu: MenuCreate_menuCreate_menu | null;
}

export interface MenuCreate {
  /**
   * Creates a new Menu
   */
  menuCreate: MenuCreate_menuCreate | null;
}

export interface MenuCreateVariables {
  input: MenuCreateInput;
}
