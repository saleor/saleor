import * as React from "react";
import FilterListIcon from "material-ui-icons/FilterList";
import Grid from "material-ui/Grid";
import IconButton from "material-ui/IconButton";
import Add from "material-ui-icons/Add";
import { Link } from "react-router-dom";
import Hidden from "material-ui/Hidden";
import Card from "material-ui/Card";
import Drawer from "material-ui/Drawer";
import { stringify as stringifyQs } from "qs";

import { TypedPageListQuery, pageListQuery } from "../queries";
import i18n from "../../i18n";
import PageListComponent from "../components/PageListComponent";
import PageHeader from "../../components/PageHeader";
import PageFilters from "../components/PageFilters";
import Navigator from "../../components/Navigator";
import { pageEditUrl, pageStorefrontUrl } from "../index";

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
      <TypedPageListQuery query={pageListQuery} variables={{ first: 4 }}>
        {({ data, loading, error, fetchMore }) => {
          if (error) {
            return <>not ok</>;
          }

          const loadNextPage = () => {
            if (loading) {
              return;
            }
            return fetchMore({
              variables: {
                first: 3,
                after: data.pages.pageInfo.endCursor
              },
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
              }
            });
          };
          const loadPreviousPage = () => {
            if (loading) {
              return;
            }
            return fetchMore({
              variables: {
                first: undefined,
                last: 12,
                before: data.pages.pageInfo.startCursor
              },
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
                                component={props => <Link to="#" {...props} />}
                                disabled={loading}
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
