/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: MenuFragment
// ====================================================

export interface MenuFragment_items {
  __typename: "MenuItem";
  /**
   * The ID of the object.
   */
  id: string;
}

export interface MenuFragment {
  __typename: "Menu";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  items: (MenuFragment_items | null)[] | null;
}
