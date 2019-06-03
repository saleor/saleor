/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { MenuItemCreateInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: MenuItemCreate
// ====================================================

export interface MenuItemCreate_menuItemCreate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu_items_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu_items_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu_items_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu_items_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu_items_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu_items_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_children_children_children_category {
  __typename: "Category";
  id: string;
  name: string;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_children_children_children_collection {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_children_children_children_page {
  __typename: "Page";
  id: string;
  title: string;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_children_children_children {
  __typename: "MenuItem";
  category: MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_children_children_children_category | null;
  collection: MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_children_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_children_children_children_page | null;
  sortOrder: number | null;
  url: string | null;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_children_children {
  __typename: "MenuItem";
  category: MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_children_children_category | null;
  collection: MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_children_children_page | null;
  sortOrder: number | null;
  url: string | null;
  children: (MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_children_children_children | null)[] | null;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_children {
  __typename: "MenuItem";
  category: MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_children_category | null;
  collection: MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_children_page | null;
  sortOrder: number | null;
  url: string | null;
  children: (MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_children_children | null)[] | null;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children {
  __typename: "MenuItem";
  category: MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_category | null;
  collection: MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_page | null;
  sortOrder: number | null;
  url: string | null;
  children: (MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children_children | null)[] | null;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children {
  __typename: "MenuItem";
  category: MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_category | null;
  collection: MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_page | null;
  sortOrder: number | null;
  url: string | null;
  children: (MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children_children | null)[] | null;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu_items_children {
  __typename: "MenuItem";
  category: MenuItemCreate_menuItemCreate_menuItem_menu_items_children_category | null;
  collection: MenuItemCreate_menuItemCreate_menuItem_menu_items_children_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemCreate_menuItemCreate_menuItem_menu_items_children_page | null;
  sortOrder: number | null;
  url: string | null;
  children: (MenuItemCreate_menuItemCreate_menuItem_menu_items_children_children | null)[] | null;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu_items {
  __typename: "MenuItem";
  category: MenuItemCreate_menuItemCreate_menuItem_menu_items_category | null;
  collection: MenuItemCreate_menuItemCreate_menuItem_menu_items_collection | null;
  id: string;
  level: number;
  name: string;
  page: MenuItemCreate_menuItemCreate_menuItem_menu_items_page | null;
  sortOrder: number | null;
  url: string | null;
  children: (MenuItemCreate_menuItemCreate_menuItem_menu_items_children | null)[] | null;
}

export interface MenuItemCreate_menuItemCreate_menuItem_menu {
  __typename: "Menu";
  id: string;
  items: (MenuItemCreate_menuItemCreate_menuItem_menu_items | null)[] | null;
}

export interface MenuItemCreate_menuItemCreate_menuItem {
  __typename: "MenuItem";
  menu: MenuItemCreate_menuItemCreate_menuItem_menu;
}

export interface MenuItemCreate_menuItemCreate {
  __typename: "MenuItemCreate";
  errors: MenuItemCreate_menuItemCreate_errors[] | null;
  menuItem: MenuItemCreate_menuItemCreate_menuItem | null;
}

export interface MenuItemCreate {
  menuItemCreate: MenuItemCreate_menuItemCreate | null;
}

export interface MenuItemCreateVariables {
  input: MenuItemCreateInput;
}
