import { stringify } from "querystring";
import * as React from "react";

import ErrorMessageCard from "../../components/ErrorMessageCard";
import Navigator from "../../components/Navigator";
import i18n from "../../i18n";
import PageListPage from "../components/PageListPage/PageListPage";
import {
  pageAddUrl,
  pageEditUrl,
  pageListUrl,
  pageStorefrontUrl
} from "../index";
import { pageListQuery, TypedPageListQuery } from "../queries";

interface PageListProps {
  params: any;
}

interface PageListState {
  isFilterMenuOpened: boolean;
}

export class PageList extends React.Component<PageListProps, PageListState> {
  state = { isFilterMenuOpened: false };
  handleFilterMenuOpen = () => {
    this.setState(prevState => ({
      isFilterMenuOpened: !prevState.isFilterMenuOpened
    }));
  };
  render() {
    const { params } = this.props;
    const PAGINATE_BY = 20;
    const paginationState =
      params && (params.before || params.after)
        ? params.after
          ? {
              after: params.after,
              first: PAGINATE_BY
            }
          : {
              before: params.before,
              last: PAGINATE_BY
            }
        : {
            first: PAGINATE_BY
          };
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

              const loadNextPage = () => {
                if (loading) {
                  return;
                }
                return navigate(
                  pageListUrl +
                    "?" +
                    stringify({
                      after: data.pages.pageInfo.endCursor
                    }),
                  true
                );
              };
              const loadPreviousPage = () => {
                if (loading) {
                  return;
                }
                return navigate(
                  pageListUrl +
                    "?" +
                    stringify({
                      before: data.pages.pageInfo.startCursor
                    }),
                  true
                );
              };
              const pageInfo =
                data && data.pages && data.pages.pageInfo
                  ? {
                      ...data.pages.pageInfo,
                      hasNextPage:
                        !!paginationState.before ||
                        data.pages.pageInfo.hasNextPage,
                      hasPreviousPage:
                        !!paginationState.after ||
                        data.pages.pageInfo.hasPreviousPage
                    }
                  : undefined;

              return (
                <Navigator>
                  {navigate => {
                    const handleEditClick = (id: string) => () =>
                      navigate(pageEditUrl(id));
                    const handleShowPageClick = (slug: string) => () =>
                      window.open(pageStorefrontUrl(slug));
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
