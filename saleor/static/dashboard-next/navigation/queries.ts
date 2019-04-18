import gql from "graphql-tag";
import { pageInfoFragment, TypedQuery } from "../queries";
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
