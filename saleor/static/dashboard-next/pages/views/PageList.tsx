import * as React from "react";

import ErrorMessageCard from "../../components/ErrorMessageCard";
import Navigator from "../../components/Navigator";
import { createPaginationState, Paginator } from "../../components/Paginator";
import i18n from "../../i18n";
import { maybe } from "../../misc";
import PageListPage from "../components/PageListPage/PageListPage";
import { TypedPageListQuery } from "../queries";
import { pageAddUrl, pageUrl } from "../urls";

export type PageListQueryParams = Partial<{ after: string; before: string }>;

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
      const handleEditClick = (id: string) => () => navigate(pageUrl(id));
      return (
        <TypedPageListQuery displayLoader variables={paginationState}>
          {({ data, loading, error }) => {
            if (error) {
              return (
                <ErrorMessageCard
                  message={i18n.t("Something went terribly wrong.")}
                />
              );
            }

            return (
              <Paginator
                pageInfo={maybe(() => data.pages.pageInfo)}
                paginationState={paginationState}
                queryString={params}
              >
                {({ loadNextPage, loadPreviousPage, pageInfo }) => (
                  <PageListPage
                    disabled={loading}
                    pages={
                      data && data.pages
                        ? data.pages.edges.map(edge => edge.node)
                        : undefined
                    }
                    pageInfo={pageInfo}
                    onAdd={() => navigate(pageAddUrl)}
                    onRowClick={handleEditClick}
                    onNextPage={loadNextPage}
                    onPreviousPage={loadPreviousPage}
                  />
                )}
              </Paginator>
            );
          }}
        </TypedPageListQuery>
      );
    }}
  </Navigator>
);

export default PageList;
