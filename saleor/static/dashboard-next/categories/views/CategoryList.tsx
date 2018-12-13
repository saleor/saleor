import * as React from "react";

import Navigator from "../../components/Navigator";
import { createPaginationState, Paginator } from "../../components/Paginator";
import { maybe } from "../../misc";
import { CategoryListPage } from "../components/CategoryListPage/CategoryListPage";
import { TypedRootCategoriesQuery } from "../queries";
import { categoryAddUrl, categoryUrl } from "../urls";

export type CategoryListQueryParams = Partial<{
  after: string;
  before: string;
}>;

interface CategoryListProps {
  params: CategoryListQueryParams;
}

const PAGINATE_BY = 20;

export const CategoryList: React.StatelessComponent<CategoryListProps> = ({
  params
}) => (
  <Navigator>
    {navigate => {
      const paginationState = createPaginationState(PAGINATE_BY, params);
      return (
        <TypedRootCategoriesQuery displayLoader variables={paginationState}>
          {({ data, loading }) => (
            <Paginator
              pageInfo={maybe(() => data.categories.pageInfo)}
              paginationState={paginationState}
              queryString={params}
            >
              {({ loadNextPage, loadPreviousPage, pageInfo }) => (
                <CategoryListPage
                  categories={maybe(
                    () => data.categories.edges.map(edge => edge.node),
                    []
                  )}
                  onAdd={() => navigate(categoryAddUrl())}
                  onRowClick={id => () => navigate(categoryUrl(id))}
                  disabled={loading}
                  onNextPage={loadNextPage}
                  onPreviousPage={loadPreviousPage}
                  pageInfo={pageInfo}
                />
              )}
            </Paginator>
          )}
        </TypedRootCategoriesQuery>
      );
    }}
  </Navigator>
);
export default CategoryList;
