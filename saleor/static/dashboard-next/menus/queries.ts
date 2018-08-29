import gql from "graphql-tag";
import { Query, QueryProps } from "react-apollo";
import { MenuListQuery, MenuListQueryVariables } from "../gql-types";

export const TypedMenuListQuery = Query as React.ComponentType<
  QueryProps<MenuListQuery, MenuListQueryVariables>
>;

export const menuListQuery = gql`
  query MenuList($first: Int, $after: String, $last: Int, $before: String) {
    menus(before: $before, after: $after, first: $first, last: $last) {
      edges {
        node {
          id
          name
          items {
            totalCount
          }
        }
      }
      pageInfo {
        hasPreviousPage
        hasNextPage
        startCursor
        endCursor
      }
    }
  }
`;
