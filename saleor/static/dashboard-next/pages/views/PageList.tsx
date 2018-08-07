import * as React from "react";

import ErrorMessageCard from "../../components/ErrorMessageCard";
import Navigator from "../../components/Navigator";
import i18n from "../../i18n";
import { createPaginationData, createPaginationState } from "../../misc";
import PageListPage from "../components/PageListPage/PageListPage";
import { pageAddUrl, pageEditUrl, pageListUrl } from "../index";
import { pageListQuery, TypedPageListQuery } from "../queries";

interface PageListProps {
  params: {
    after?: string;
    before?: string;
  };
}

interface PageListState {
  isFilterMenuOpened: boolean;
}

const PAGINATE_BY = 20;

export class PageList extends React.Component<PageListProps, PageListState> {
  state = { isFilterMenuOpened: false };
  handleFilterMenuOpen = () => {
    this.setState(prevState => ({
      isFilterMenuOpened: !prevState.isFilterMenuOpened
    }));
  };
  render() {
    const { params } = this.props;
    const paginationState = createPaginationState(PAGINATE_BY, params);
    return (
      <Navigator>
        {navigate => (
          <TypedPageListQuery
            query={pageListQuery}
            variables={paginationState}
            fetchPolicy="network-only"
          >
            {({ data, loading, error }) => {
              if (error) {
                return (
                  <ErrorMessageCard
                    message={i18n.t("Something went terribly wrong.")}
                  />
                );
              }

              const {
                loadNextPage,
                loadPreviousPage,
                pageInfo
              } = createPaginationData(
                navigate,
                paginationState,
                pageListUrl,
                data && data.pages ? data.pages.pageInfo : undefined,
                loading
              );

              return (
                <Navigator>
                  {navigate => {
                    const handleEditClick = (id: string) => () =>
                      navigate(pageEditUrl(id));
                    return (
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
                    );
                  }}
                </Navigator>
              );
            }}
          </TypedPageListQuery>
        )}
      </Navigator>
    );
  }
}

export default PageList;
