import Add from "@material-ui/icons/Add";
import FilterListIcon from "@material-ui/icons/FilterList";
import Card from "material-ui/Card";
import Drawer from "material-ui/Drawer";
import Grid from "material-ui/Grid";
import Hidden from "material-ui/Hidden";
import IconButton from "material-ui/IconButton";
import { stringify as stringifyQs } from "qs";
import * as React from "react";
import { Link } from "react-router-dom";

import ErrorMessageCard from "../../components/ErrorMessageCard";
import Navigator from "../../components/Navigator";
import PageHeader from "../../components/PageHeader";
import i18n from "../../i18n";
import PageListComponent from "../components/PageList";
import PageListPage from "../components/PageListPage/PageListPage";
import { pageAddUrl, pageEditUrl, pageStorefrontUrl } from "../index";
import { pageListQuery, TypedPageListQuery } from "../queries";

interface PageListProps {
  filters: any;
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
    const { filters } = this.props;
    return (
      <TypedPageListQuery
        query={pageListQuery}
        variables={{ first: 4 }}
        fetchPolicy="network-only"
      >
        {({ data, loading, error, fetchMore }) => {
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
            return fetchMore({
              updateQuery: (previousResult, { fetchMoreResult }) => {
                return {
                  ...fetchMoreResult,
                  pages: {
                    ...fetchMoreResult.pages,
                    pageInfo: {
                      ...fetchMoreResult.pages.pageInfo,
                      hasPreviousPage: true
                    }
                  }
                };
              },
              variables: {
                after: data.pages.pageInfo.endCursor,
                first: 12
              }
            });
          };
          const loadPreviousPage = () => {
            if (loading) {
              return;
            }
            return fetchMore({
              updateQuery: (previousResult, { fetchMoreResult, variables }) => {
                return {
                  ...fetchMoreResult,
                  pages: {
                    ...fetchMoreResult.pages,
                    pageInfo: {
                      ...fetchMoreResult.pages.pageInfo,
                      hasNextPage: true
                    }
                  }
                };
              },
              variables: {
                before: data.pages.pageInfo.startCursor,
                first: undefined,
                last: 12
              }
            });
          };

          return (
            <Navigator>
              {navigate => {
                const handleEditClick = (id: string) => () =>
                  navigate(pageEditUrl(id));
                const handleShowPageClick = (slug: string) => () =>
                  window.open(pageStorefrontUrl(slug));
                return (
                  <PageListPage
                    pages={
                      data && data.pages
                        ? data.pages.edges.map(edge => edge.node)
                        : undefined
                    }
                    pageInfo={
                      data && data.pages && data.pages.pageInfo
                        ? data.pages.pageInfo
                        : undefined
                    }
                    onAddPage={() => navigate(pageAddUrl)}
                    onEditPage={handleEditClick}
                    onNextPage={loadNextPage}
                    onPreviousPage={loadPreviousPage}
                    onShowPage={handleShowPageClick}
                  />
                );
              }}
            </Navigator>
          );
        }}
      </TypedPageListQuery>
    );
  }
}

export default PageList;
