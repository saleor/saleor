import * as React from "react";

import Navigator from "../../components/Navigator";
import { createPaginationState, Paginator } from "../../components/Paginator";
import { configurationMenuUrl } from "../../configuration";
import { maybe } from "../../misc";
import PageListPage from "../components/PageListPage/PageListPage";
import { TypedPageListQuery } from "../queries";
import { pageCreateUrl, pageUrl } from "../urls";

export type PageListQueryParams = Partial<{
  after: string;
  before: string;
}>;

interface PageListProps {
  params: PageListQueryParams;
}

const PAGINATE_BY = 20;

export const PageList: React.StatelessComponent<PageListProps> = ({
  params
}) => (
  <Navigator>
    {navigate => {
      const paginationState = createPaginationState(PAGINATE_BY, params);

      return (
        <TypedPageListQuery displayLoader variables={paginationState}>
          {({ data, loading }) => (
            <Paginator
              pageInfo={maybe(() => data.pages.pageInfo)}
              paginationState={paginationState}
              queryString={params}
            >
              {({ loadNextPage, loadPreviousPage, pageInfo }) => (
                <PageListPage
                  disabled={loading}
                  pages={maybe(() => data.pages.edges.map(edge => edge.node))}
                  pageInfo={pageInfo}
                  onAdd={() => navigate(pageCreateUrl)}
                  onBack={() => navigate(configurationMenuUrl)}
                  onNextPage={loadNextPage}
                  onPreviousPage={loadPreviousPage}
                  onRowClick={id => () => navigate(pageUrl(id))}
                />
              )}
            </Paginator>
          )}
        </TypedPageListQuery>
      );
    }}
  </Navigator>
);

export default PageList;
