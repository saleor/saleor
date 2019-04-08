import { stringify as stringifyQs } from "qs";

import { PageInfo, PaginationState } from "../components/Paginator";
import { Pagination } from "../types";
import useNavigator from "./useNavigator";

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
