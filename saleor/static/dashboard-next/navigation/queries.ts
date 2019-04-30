import gql from "graphql-tag";
import { pageInfoFragment, TypedQuery } from "../queries";
import { MenuDetails, MenuDetailsVariables } from "./types/MenuDetails";
import { MenuList, MenuListVariables } from "./types/MenuList";

const menuFragment = gql`
  fragment MenuFragment on Menu {
    id
    name
    items {
      id
    }
  }
`;

const menuItemFragment = gql`
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

// GraphQL does not support recurive fragments
const menuDetails = gql`
  ${menuItemFragment}
  query MenuDetails($id: ID!) {
    menu(id: $id) {
      id
      items {
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
      name
    }
  }
`;
export const MenuDetailsQuery = TypedQuery<MenuDetails, MenuDetailsVariables>(
  menuDetails
);
