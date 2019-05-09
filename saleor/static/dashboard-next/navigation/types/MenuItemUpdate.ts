/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { MenuItemMoveInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: MenuItemUpdate
// ====================================================

export interface MenuItemUpdate_menuUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface MenuItemUpdate_menuUpdate_menu_items_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuUpdate_menu_items_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuUpdate_menu_items_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemUpdate_menuUpdate_menu_items_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuUpdate_menu_items_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuUpdate_menu_items_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemUpdate_menuUpdate_menu_items_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuUpdate_menu_items_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuUpdate_menu_items_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemUpdate_menuUpdate_menu_items_children_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuUpdate_menu_items_children_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuUpdate_menu_items_children_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemUpdate_menuUpdate_menu_items_children_children_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuUpdate_menu_items_children_children_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuUpdate_menu_items_children_children_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemUpdate_menuUpdate_menu_items_children_children_children_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuUpdate_menu_items_children_children_children_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuUpdate_menu_items_children_children_children_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemUpdate_menuUpdate_menu_items_children_children_children_children_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuUpdate_menu_items_children_children_children_children_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuUpdate_menu_items_children_children_children_children_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemUpdate_menuUpdate_menu_items_children_children_children_children_children_children {
  __typename: "MenuItem";
  category: MenuItemUpdate_menuUpdate_menu_items_children_children_children_children_children_children_category | null;
  collection: MenuItemUpdate_menuUpdate_menu_items_children_children_children_children_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemUpdate_menuUpdate_menu_items_children_children_children_children_children_children_page | null;
  sortOrder: number;
  url: string | null;
}

export interface MenuItemUpdate_menuUpdate_menu_items_children_children_children_children_children {
  __typename: "MenuItem";
  category: MenuItemUpdate_menuUpdate_menu_items_children_children_children_children_children_category | null;
  collection: MenuItemUpdate_menuUpdate_menu_items_children_children_children_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemUpdate_menuUpdate_menu_items_children_children_children_children_children_page | null;
  sortOrder: number;
  url: string | null;
  children: (MenuItemUpdate_menuUpdate_menu_items_children_children_children_children_children_children | null)[] | null;
}

export interface MenuItemUpdate_menuUpdate_menu_items_children_children_children_children {
  __typename: "MenuItem";
  category: MenuItemUpdate_menuUpdate_menu_items_children_children_children_children_category | null;
  collection: MenuItemUpdate_menuUpdate_menu_items_children_children_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemUpdate_menuUpdate_menu_items_children_children_children_children_page | null;
  sortOrder: number;
  url: string | null;
  children: (MenuItemUpdate_menuUpdate_menu_items_children_children_children_children_children | null)[] | null;
}

export interface MenuItemUpdate_menuUpdate_menu_items_children_children_children {
  __typename: "MenuItem";
  category: MenuItemUpdate_menuUpdate_menu_items_children_children_children_category | null;
  collection: MenuItemUpdate_menuUpdate_menu_items_children_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemUpdate_menuUpdate_menu_items_children_children_children_page | null;
  sortOrder: number;
  url: string | null;
  children: (MenuItemUpdate_menuUpdate_menu_items_children_children_children_children | null)[] | null;
}

export interface MenuItemUpdate_menuUpdate_menu_items_children_children {
  __typename: "MenuItem";
  category: MenuItemUpdate_menuUpdate_menu_items_children_children_category | null;
  collection: MenuItemUpdate_menuUpdate_menu_items_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemUpdate_menuUpdate_menu_items_children_children_page | null;
  sortOrder: number;
  url: string | null;
  children: (MenuItemUpdate_menuUpdate_menu_items_children_children_children | null)[] | null;
}

export interface MenuItemUpdate_menuUpdate_menu_items_children {
  __typename: "MenuItem";
  category: MenuItemUpdate_menuUpdate_menu_items_children_category | null;
  collection: MenuItemUpdate_menuUpdate_menu_items_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemUpdate_menuUpdate_menu_items_children_page | null;
  sortOrder: number;
  url: string | null;
  children: (MenuItemUpdate_menuUpdate_menu_items_children_children | null)[] | null;
}

export interface MenuItemUpdate_menuUpdate_menu_items {
  __typename: "MenuItem";
  category: MenuItemUpdate_menuUpdate_menu_items_category | null;
  collection: MenuItemUpdate_menuUpdate_menu_items_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemUpdate_menuUpdate_menu_items_page | null;
  sortOrder: number;
  url: string | null;
  children: (MenuItemUpdate_menuUpdate_menu_items_children | null)[] | null;
}

export interface MenuItemUpdate_menuUpdate_menu {
  __typename: "Menu";
  id: string;
  items: (MenuItemUpdate_menuUpdate_menu_items | null)[] | null;
  name: string;
}

export interface MenuItemUpdate_menuUpdate {
  __typename: "MenuUpdate";
  errors: MenuItemUpdate_menuUpdate_errors[] | null;
  menu: MenuItemUpdate_menuUpdate_menu | null;
}

export interface MenuItemUpdate_menuItemMove_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface MenuItemUpdate_menuItemMove_menu_items_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuItemMove_menu_items_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuItemMove_menu_items_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemUpdate_menuItemMove_menu_items_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuItemMove_menu_items_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuItemMove_menu_items_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemUpdate_menuItemMove_menu_items_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuItemMove_menu_items_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuItemMove_menu_items_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemUpdate_menuItemMove_menu_items_children_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuItemMove_menu_items_children_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuItemMove_menu_items_children_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemUpdate_menuItemMove_menu_items_children_children_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuItemMove_menu_items_children_children_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuItemMove_menu_items_children_children_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemUpdate_menuItemMove_menu_items_children_children_children_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuItemMove_menu_items_children_children_children_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuItemMove_menu_items_children_children_children_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemUpdate_menuItemMove_menu_items_children_children_children_children_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuItemMove_menu_items_children_children_children_children_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemUpdate_menuItemMove_menu_items_children_children_children_children_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemUpdate_menuItemMove_menu_items_children_children_children_children_children_children {
  __typename: "MenuItem";
  category: MenuItemUpdate_menuItemMove_menu_items_children_children_children_children_children_children_category | null;
  collection: MenuItemUpdate_menuItemMove_menu_items_children_children_children_children_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemUpdate_menuItemMove_menu_items_children_children_children_children_children_children_page | null;
  sortOrder: number;
  url: string | null;
}

export interface MenuItemUpdate_menuItemMove_menu_items_children_children_children_children_children {
  __typename: "MenuItem";
  category: MenuItemUpdate_menuItemMove_menu_items_children_children_children_children_children_category | null;
  collection: MenuItemUpdate_menuItemMove_menu_items_children_children_children_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemUpdate_menuItemMove_menu_items_children_children_children_children_children_page | null;
  sortOrder: number;
  url: string | null;
  children: (MenuItemUpdate_menuItemMove_menu_items_children_children_children_children_children_children | null)[] | null;
}

export interface MenuItemUpdate_menuItemMove_menu_items_children_children_children_children {
  __typename: "MenuItem";
  category: MenuItemUpdate_menuItemMove_menu_items_children_children_children_children_category | null;
  collection: MenuItemUpdate_menuItemMove_menu_items_children_children_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemUpdate_menuItemMove_menu_items_children_children_children_children_page | null;
  sortOrder: number;
  url: string | null;
  children: (MenuItemUpdate_menuItemMove_menu_items_children_children_children_children_children | null)[] | null;
}

export interface MenuItemUpdate_menuItemMove_menu_items_children_children_children {
  __typename: "MenuItem";
  category: MenuItemUpdate_menuItemMove_menu_items_children_children_children_category | null;
  collection: MenuItemUpdate_menuItemMove_menu_items_children_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemUpdate_menuItemMove_menu_items_children_children_children_page | null;
  sortOrder: number;
  url: string | null;
  children: (MenuItemUpdate_menuItemMove_menu_items_children_children_children_children | null)[] | null;
}

export interface MenuItemUpdate_menuItemMove_menu_items_children_children {
  __typename: "MenuItem";
  category: MenuItemUpdate_menuItemMove_menu_items_children_children_category | null;
  collection: MenuItemUpdate_menuItemMove_menu_items_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemUpdate_menuItemMove_menu_items_children_children_page | null;
  sortOrder: number;
  url: string | null;
  children: (MenuItemUpdate_menuItemMove_menu_items_children_children_children | null)[] | null;
}

export interface MenuItemUpdate_menuItemMove_menu_items_children {
  __typename: "MenuItem";
  category: MenuItemUpdate_menuItemMove_menu_items_children_category | null;
  collection: MenuItemUpdate_menuItemMove_menu_items_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemUpdate_menuItemMove_menu_items_children_page | null;
  sortOrder: number;
  url: string | null;
  children: (MenuItemUpdate_menuItemMove_menu_items_children_children | null)[] | null;
}

export interface MenuItemUpdate_menuItemMove_menu_items {
  __typename: "MenuItem";
  category: MenuItemUpdate_menuItemMove_menu_items_category | null;
  collection: MenuItemUpdate_menuItemMove_menu_items_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemUpdate_menuItemMove_menu_items_page | null;
  sortOrder: number;
  url: string | null;
  children: (MenuItemUpdate_menuItemMove_menu_items_children | null)[] | null;
}

export interface MenuItemUpdate_menuItemMove_menu {
  __typename: "Menu";
  id: string;
  items: (MenuItemUpdate_menuItemMove_menu_items | null)[] | null;
  name: string;
}

export interface MenuItemUpdate_menuItemMove {
  __typename: "MenuItemMove";
  errors: MenuItemUpdate_menuItemMove_errors[] | null;
  menu: MenuItemUpdate_menuItemMove_menu | null;
}

export interface MenuItemUpdate {
  menuUpdate: MenuItemUpdate_menuUpdate | null;
  menuItemMove: MenuItemUpdate_menuItemMove | null;
}

export interface MenuItemUpdateVariables {
  id: string;
  name: string;
  moves: (MenuItemMoveInput | null)[];
}
