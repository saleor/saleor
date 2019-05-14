import { stringify as stringifyQs } from "qs";

import { Pagination } from "../types";
import useNavigator from "./useNavigator";

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

export function createPaginationState(
  paginateBy: number,
  queryString: Pagination
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

function usePaginator() {
  const navigate = useNavigator();

  function paginate(
    pageInfo: PageInfo,
    paginationState: PaginationState,
    queryString: Pagination
  ) {
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

    return {
      loadNextPage,
      loadPreviousPage,
      pageInfo: newPageInfo
    };
  }
  return paginate;
}
export default usePaginator;
