/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: MenuFragment
// ====================================================

export interface MenuFragment_items {
  __typename: "MenuItem";
  id: string;
}

export interface MenuFragment {
  __typename: "Menu";
  id: string;
  name: string;
  items: (MenuFragment_items | null)[] | null;
}
