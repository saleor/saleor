import { stringify as stringifyQs } from "qs";
import * as React from "react";

import Navigator from "./Navigator";

export interface PageInfo {
  endCursor: string;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string;
}
export interface PaginationState {
  after?: string;
  before?: string;
  first?: number;
  last?: number;
}

interface QueryString {
  after?: string;
  before?: string;
}

interface PaginatorProps {
  children: (props: {
    loadNextPage: () => void;
    loadPreviousPage: () => void;
    pageInfo: PageInfo;
  }) => React.ReactElement<any>;
  pageInfo: PageInfo;
  paginationState: PaginationState;
  queryString: QueryString;
}

export function createPaginationState(
  paginateBy: number,
  queryString: QueryString
): PaginationState {
  return queryString && (queryString.before || queryString.after)
    ? queryString.after
      ? {
          after: queryString.after,
          first: paginateBy
        }
      : {
          before: queryString.before,
          last: paginateBy
        }
    : {
        first: paginateBy
      };
}

export const Paginator: React.StatelessComponent<PaginatorProps> = ({
  children,
  pageInfo,
  paginationState,
  queryString
}) => (
  <Navigator>
    {navigate => {
      const loadNextPage = () =>
        navigate(
          "?" +
            stringifyQs({
              ...queryString,
              after: pageInfo.endCursor,
              before: undefined
            }),
          true
        );

      const loadPreviousPage = () =>
        navigate(
          "?" +
            stringifyQs({
              ...queryString,
              after: undefined,
              before: pageInfo.startCursor
            }),
          true
        );

      const newPageInfo = pageInfo
        ? {
            ...pageInfo,
            hasNextPage: !!paginationState.before || pageInfo.hasNextPage,
            hasPreviousPage: !!paginationState.after || pageInfo.hasPreviousPage
          }
        : undefined;

      return children({
        loadNextPage,
        loadPreviousPage,
        pageInfo: newPageInfo
      });
    }}
  </Navigator>
);
