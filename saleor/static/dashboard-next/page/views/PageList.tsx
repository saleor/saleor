import Add from "material-ui-icons/Add";
import FilterListIcon from "material-ui-icons/FilterList";
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
import PageFilters from "../components/PageFilters";
import PageListComponent from "../components/PageList";
import { pageEditUrl, pageStorefrontUrl } from "../index";
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
                first: 3
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
                const applyFilters = data => {
                  navigate(
                    `?${stringifyQs({ ...filters, ...data.formData })}`,
                    true
                  );
                };
                const clearFilters = () => navigate("?");
                return (
                  <Grid container spacing={16}>
                    <Grid item xs={12}>
                      <Grid container spacing={16}>
                        <Grid item xs={12} md={9}>
                          <Card>
                            <PageHeader
                              title={i18n.t("Pages", {
                                context: "title"
                              })}
                            >
                              <IconButton
                                disabled={loading}
                                onClick={() => navigate("/pages/add/")}
                              >
                                <Add />
                              </IconButton>
                              <Hidden mdUp>
                                <IconButton
                                  disabled={loading}
                                  onClick={this.handleFilterMenuOpen}
                                >
                                  <FilterListIcon />
                                </IconButton>
                              </Hidden>
                            </PageHeader>
                            <PageListComponent
                              pageInfo={loading ? null : data.pages.pageInfo}
                              pages={loading ? null : data.pages.edges}
                              handlePreviousPage={loadPreviousPage}
                              handleNextPage={loadNextPage}
                              editPageUrl={pageEditUrl}
                              showPageUrl={pageStorefrontUrl}
                              loading={loading}
                            />
                          </Card>
                        </Grid>
                        <Grid item xs={12} md={3}>
                          <Hidden smDown>
                            <PageFilters
                              handleSubmit={applyFilters}
                              handleClear={clearFilters}
                              formState={filters}
                            />
                          </Hidden>
                          <Drawer
                            open={this.state.isFilterMenuOpened}
                            onClose={this.handleFilterMenuOpen}
                            anchor="bottom"
                          >
                            <PageFilters
                              handleSubmit={applyFilters}
                              handleClear={clearFilters}
                              formState={filters}
                            />
                          </Drawer>
                        </Grid>
                      </Grid>
                    </Grid>
                  </Grid>
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
