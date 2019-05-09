/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { MenuItemMoveInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: MenuUpdate
// ====================================================

export interface MenuUpdate_menuUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface MenuUpdate_menuUpdate_menu_items_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuUpdate_menuUpdate_menu_items_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuUpdate_menuUpdate_menu_items_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuUpdate_menuUpdate_menu_items_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuUpdate_menuUpdate_menu_items_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuUpdate_menuUpdate_menu_items_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuUpdate_menuUpdate_menu_items_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuUpdate_menuUpdate_menu_items_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuUpdate_menuUpdate_menu_items_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuUpdate_menuUpdate_menu_items_children_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuUpdate_menuUpdate_menu_items_children_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuUpdate_menuUpdate_menu_items_children_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuUpdate_menuUpdate_menu_items_children_children_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuUpdate_menuUpdate_menu_items_children_children_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuUpdate_menuUpdate_menu_items_children_children_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuUpdate_menuUpdate_menu_items_children_children_children_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuUpdate_menuUpdate_menu_items_children_children_children_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuUpdate_menuUpdate_menu_items_children_children_children_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuUpdate_menuUpdate_menu_items_children_children_children_children_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuUpdate_menuUpdate_menu_items_children_children_children_children_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuUpdate_menuUpdate_menu_items_children_children_children_children_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuUpdate_menuUpdate_menu_items_children_children_children_children_children_children {
  __typename: "MenuItem";
  category: MenuUpdate_menuUpdate_menu_items_children_children_children_children_children_children_category | null;
  collection: MenuUpdate_menuUpdate_menu_items_children_children_children_children_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuUpdate_menuUpdate_menu_items_children_children_children_children_children_children_page | null;
  sortOrder: number;
  url: string | null;
}

export interface MenuUpdate_menuUpdate_menu_items_children_children_children_children_children {
  __typename: "MenuItem";
  category: MenuUpdate_menuUpdate_menu_items_children_children_children_children_children_category | null;
  collection: MenuUpdate_menuUpdate_menu_items_children_children_children_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuUpdate_menuUpdate_menu_items_children_children_children_children_children_page | null;
  sortOrder: number;
  url: string | null;
  children: (MenuUpdate_menuUpdate_menu_items_children_children_children_children_children_children | null)[] | null;
}

export interface MenuUpdate_menuUpdate_menu_items_children_children_children_children {
  __typename: "MenuItem";
  category: MenuUpdate_menuUpdate_menu_items_children_children_children_children_category | null;
  collection: MenuUpdate_menuUpdate_menu_items_children_children_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuUpdate_menuUpdate_menu_items_children_children_children_children_page | null;
  sortOrder: number;
  url: string | null;
  children: (MenuUpdate_menuUpdate_menu_items_children_children_children_children_children | null)[] | null;
}

export interface MenuUpdate_menuUpdate_menu_items_children_children_children {
  __typename: "MenuItem";
  category: MenuUpdate_menuUpdate_menu_items_children_children_children_category | null;
  collection: MenuUpdate_menuUpdate_menu_items_children_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuUpdate_menuUpdate_menu_items_children_children_children_page | null;
  sortOrder: number;
  url: string | null;
  children: (MenuUpdate_menuUpdate_menu_items_children_children_children_children | null)[] | null;
}

export interface MenuUpdate_menuUpdate_menu_items_children_children {
  __typename: "MenuItem";
  category: MenuUpdate_menuUpdate_menu_items_children_children_category | null;
  collection: MenuUpdate_menuUpdate_menu_items_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuUpdate_menuUpdate_menu_items_children_children_page | null;
  sortOrder: number;
  url: string | null;
  children: (MenuUpdate_menuUpdate_menu_items_children_children_children | null)[] | null;
}

export interface MenuUpdate_menuUpdate_menu_items_children {
  __typename: "MenuItem";
  category: MenuUpdate_menuUpdate_menu_items_children_category | null;
  collection: MenuUpdate_menuUpdate_menu_items_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuUpdate_menuUpdate_menu_items_children_page | null;
  sortOrder: number;
  url: string | null;
  children: (MenuUpdate_menuUpdate_menu_items_children_children | null)[] | null;
}

export interface MenuUpdate_menuUpdate_menu_items {
  __typename: "MenuItem";
  category: MenuUpdate_menuUpdate_menu_items_category | null;
  collection: MenuUpdate_menuUpdate_menu_items_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuUpdate_menuUpdate_menu_items_page | null;
  sortOrder: number;
  url: string | null;
  children: (MenuUpdate_menuUpdate_menu_items_children | null)[] | null;
}

export interface MenuUpdate_menuUpdate_menu {
  __typename: "Menu";
  id: string;
  items: (MenuUpdate_menuUpdate_menu_items | null)[] | null;
  name: string;
}

export interface MenuUpdate_menuUpdate {
  __typename: "MenuUpdate";
  errors: MenuUpdate_menuUpdate_errors[] | null;
  menu: MenuUpdate_menuUpdate_menu | null;
}

export interface MenuUpdate_menuItemMove_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface MenuUpdate_menuItemMove_menu_items_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuUpdate_menuItemMove_menu_items_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuUpdate_menuItemMove_menu_items_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuUpdate_menuItemMove_menu_items_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuUpdate_menuItemMove_menu_items_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuUpdate_menuItemMove_menu_items_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuUpdate_menuItemMove_menu_items_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuUpdate_menuItemMove_menu_items_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuUpdate_menuItemMove_menu_items_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuUpdate_menuItemMove_menu_items_children_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuUpdate_menuItemMove_menu_items_children_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuUpdate_menuItemMove_menu_items_children_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuUpdate_menuItemMove_menu_items_children_children_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuUpdate_menuItemMove_menu_items_children_children_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuUpdate_menuItemMove_menu_items_children_children_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuUpdate_menuItemMove_menu_items_children_children_children_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuUpdate_menuItemMove_menu_items_children_children_children_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuUpdate_menuItemMove_menu_items_children_children_children_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuUpdate_menuItemMove_menu_items_children_children_children_children_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuUpdate_menuItemMove_menu_items_children_children_children_children_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuUpdate_menuItemMove_menu_items_children_children_children_children_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuUpdate_menuItemMove_menu_items_children_children_children_children_children_children {
  __typename: "MenuItem";
  category: MenuUpdate_menuItemMove_menu_items_children_children_children_children_children_children_category | null;
  collection: MenuUpdate_menuItemMove_menu_items_children_children_children_children_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuUpdate_menuItemMove_menu_items_children_children_children_children_children_children_page | null;
  sortOrder: number;
  url: string | null;
}

export interface MenuUpdate_menuItemMove_menu_items_children_children_children_children_children {
  __typename: "MenuItem";
  category: MenuUpdate_menuItemMove_menu_items_children_children_children_children_children_category | null;
  collection: MenuUpdate_menuItemMove_menu_items_children_children_children_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuUpdate_menuItemMove_menu_items_children_children_children_children_children_page | null;
  sortOrder: number;
  url: string | null;
  children: (MenuUpdate_menuItemMove_menu_items_children_children_children_children_children_children | null)[] | null;
}

export interface MenuUpdate_menuItemMove_menu_items_children_children_children_children {
  __typename: "MenuItem";
  category: MenuUpdate_menuItemMove_menu_items_children_children_children_children_category | null;
  collection: MenuUpdate_menuItemMove_menu_items_children_children_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuUpdate_menuItemMove_menu_items_children_children_children_children_page | null;
  sortOrder: number;
  url: string | null;
  children: (MenuUpdate_menuItemMove_menu_items_children_children_children_children_children | null)[] | null;
}

export interface MenuUpdate_menuItemMove_menu_items_children_children_children {
  __typename: "MenuItem";
  category: MenuUpdate_menuItemMove_menu_items_children_children_children_category | null;
  collection: MenuUpdate_menuItemMove_menu_items_children_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuUpdate_menuItemMove_menu_items_children_children_children_page | null;
  sortOrder: number;
  url: string | null;
  children: (MenuUpdate_menuItemMove_menu_items_children_children_children_children | null)[] | null;
}

export interface MenuUpdate_menuItemMove_menu_items_children_children {
  __typename: "MenuItem";
  category: MenuUpdate_menuItemMove_menu_items_children_children_category | null;
  collection: MenuUpdate_menuItemMove_menu_items_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuUpdate_menuItemMove_menu_items_children_children_page | null;
  sortOrder: number;
  url: string | null;
  children: (MenuUpdate_menuItemMove_menu_items_children_children_children | null)[] | null;
}

export interface MenuUpdate_menuItemMove_menu_items_children {
  __typename: "MenuItem";
  category: MenuUpdate_menuItemMove_menu_items_children_category | null;
  collection: MenuUpdate_menuItemMove_menu_items_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuUpdate_menuItemMove_menu_items_children_page | null;
  sortOrder: number;
  url: string | null;
  children: (MenuUpdate_menuItemMove_menu_items_children_children | null)[] | null;
}

export interface MenuUpdate_menuItemMove_menu_items {
  __typename: "MenuItem";
  category: MenuUpdate_menuItemMove_menu_items_category | null;
  collection: MenuUpdate_menuItemMove_menu_items_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuUpdate_menuItemMove_menu_items_page | null;
  sortOrder: number;
  url: string | null;
  children: (MenuUpdate_menuItemMove_menu_items_children | null)[] | null;
}

export interface MenuUpdate_menuItemMove_menu {
  __typename: "Menu";
  id: string;
  items: (MenuUpdate_menuItemMove_menu_items | null)[] | null;
  name: string;
}

export interface MenuUpdate_menuItemMove {
  __typename: "MenuItemMove";
  errors: MenuUpdate_menuItemMove_errors[] | null;
  menu: MenuUpdate_menuItemMove_menu | null;
}

export interface MenuUpdate_menuItemBulkDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface MenuUpdate_menuItemBulkDelete {
  __typename: "MenuItemBulkDelete";
  errors: MenuUpdate_menuItemBulkDelete_errors[] | null;
}

export interface MenuUpdate {
  menuUpdate: MenuUpdate_menuUpdate | null;
  menuItemMove: MenuUpdate_menuItemMove | null;
  menuItemBulkDelete: MenuUpdate_menuItemBulkDelete | null;
}

export interface MenuUpdateVariables {
  id: string;
  name: string;
  moves: (MenuItemMoveInput | null)[];
  removeIds: (string | null)[];
}
