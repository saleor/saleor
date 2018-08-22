import { stringify } from "qs";

export interface PageInfo {
  endCursor: string;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string;
}
interface PaginationState {
  after?: string;
  before?: string;
  first?: number;
  last?: number;
}

interface QueryString {
  after?: string;
  before?: string;
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

export function createPaginationData(
  navigate: ((url: string, push: boolean) => void),
  paginationState: PaginationState,
  url: string,
  pageInfo: PageInfo,
  loading
) {
  const loadNextPage = () => {
    if (loading) {
      return;
    }
    return navigate(
      url +
        "?" +
        stringify({
          after: encodeURIComponent(pageInfo.endCursor)
        }),
      true
    );
  };
  const loadPreviousPage = () => {
    if (loading) {
      return;
    }
    return navigate(
      url +
        "?" +
        stringify({
          before: encodeURIComponent(pageInfo.startCursor)
        }),
      true
    );
  };
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

export function renderCollection<T>(
  collection: T[],
  renderItem: (
    item: T | undefined,
    index: number | undefined,
    collection: T[]
  ) => any,
  renderEmpty: (collection: T[]) => any
) {
  if (collection === undefined) {
    return renderItem(undefined, undefined, collection);
  }
  if (collection.length === 0) {
    return renderEmpty(collection);
  }
  return collection.map(renderItem);
}

export function decimal(value: string) {
  return value === "" ? null : value;
}

export const removeDoubleSlashes = (url: string) =>
  url.replace(/([^:]\/)\/+/g, "$1");
