import gql from "graphql-tag";
import { pageInfoFragment, TypedQuery } from "../queries";
import { MenuDetails, MenuDetailsVariables } from "./types/MenuDetails";
import { MenuList, MenuListVariables } from "./types/MenuList";

export const menuFragment = gql`
  fragment MenuFragment on Menu {
    id
    name
    items {
      id
    }
  }
`;

export const menuItemFragment = gql`
  fragment MenuItemFragment on MenuItem {
    category {
      id
      name
    }
    collection {
      id
      name
    }
    id
    level
    name
    page {
      id
      title
    }
    sortOrder
    url
  }
`;

// GraphQL does not support recurive fragments
export const menuItemNestedFragment = gql`
  ${menuItemFragment}
  fragment MenuItemNestedFragment on MenuItem {
    ...MenuItemFragment
    children {
      ...MenuItemFragment
      children {
        ...MenuItemFragment
        children {
          ...MenuItemFragment
          children {
            ...MenuItemFragment
            children {
              ...MenuItemFragment
              children {
                ...MenuItemFragment
              }
            }
          }
        }
      }
    }
  }
`;

export const menuDetailsFragment = gql`
  ${menuItemNestedFragment}
  fragment MenuDetailsFragment on Menu {
    id
    items {
      ...MenuItemNestedFragment
    }
    name
  }
`;

const menuList = gql`
  ${menuFragment}
  ${pageInfoFragment}
  query MenuList($first: Int, $after: String, $last: Int, $before: String) {
    menus(first: $first, after: $after, before: $before, last: $last) {
      edges {
        node {
          ...MenuFragment
        }
      }
      pageInfo {
        ...PageInfoFragment
      }
    }
  }
`;
export const MenuListQuery = TypedQuery<MenuList, MenuListVariables>(menuList);

const menuDetails = gql`
  ${menuDetailsFragment}
  query MenuDetails($id: ID!) {
    menu(id: $id) {
      ...MenuDetailsFragment
    }
  }
`;
export const MenuDetailsQuery = TypedQuery<MenuDetails, MenuDetailsVariables>(
  menuDetails
);
