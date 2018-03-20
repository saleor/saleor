import AddIcon from "material-ui-icons/Add";
import FilterListIcon from "material-ui-icons/FilterList";
import Card from "material-ui/Card";
import Drawer from "material-ui/Drawer";
import Grid from "material-ui/Grid";
import Hidden from "material-ui/Hidden";
import IconButton from "material-ui/IconButton";
import { withStyles, WithStyles } from "material-ui/styles";
import { stringify as stringifyQs } from "qs";
import * as React from "react";
import { Link } from "react-router-dom";

import ErrorMessageCard from "../../components/cards/ErrorMessageCard";
import Navigator, { NavigatorLink } from "../../components/Navigator";
import PageHeader from "../../components/PageHeader";
import i18n from "../../i18n";
import CategoryProducts from "../components/CategoryProducts";
import CategoryProperties from "../components/CategoryProperties";
import CategorySubcategories from "../components/CategorySubcategories";
import ProductFilters from "../components/ProductFilters";
import RootCategoryList from "../components/RootCategoryList";
import { categoryAddUrl } from "../index";
import {
  categoryPropertiesQuery,
  rootCategoryChildrenQuery,
  TypedCategoryPropertiesQuery,
  TypedRootCategoryChildrenQuery
} from "../queries";

const { Component } = React;

interface CategoryDetailsProps {
  filters: any;
  id: string;
}
interface CategoryDetailsState {
  isFilterMenuOpened: boolean;
}

// TODO: Replace when API is ready
const dummyProductTypes = [
  { id: "123123123", name: "Type 1" },
  { id: "123123124", name: "Type 2" },
  { id: "123123125", name: "Type 3" },
  { id: "123123126", name: "Type 4" }
];

class CategoryDetails extends Component<
  CategoryDetailsProps,
  CategoryDetailsState
> {
  state = { isFilterMenuOpened: false };

  handleFilterMenuOpen = () => {
    this.setState(prevState => ({
      isFilterMenuOpened: !prevState.isFilterMenuOpened
    }));
  };

  render() {
    const { filters, id } = this.props;
    if (id) {
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
              <TypedCategoryPropertiesQuery
                query={categoryPropertiesQuery}
                variables={{ id, first: 12 }}
                fetchPolicy="network-only"
              >
                {({ loading, error, data, fetchMore }) => {
                  if (error) {
                    return (
                      <Grid container spacing={16}>
                        <Grid item xs={12} md={9}>
                          <ErrorMessageCard message="Unable to find a matching category." />
                        </Grid>
                      </Grid>
                    );
                  }
                  const { category } = data;
                  const loadNextPage = () => {
                    if (loading) {
                      return;
                    }
                    return fetchMore({
                      updateQuery: (previousResult, { fetchMoreResult }) => {
                        return {
                          ...fetchMoreResult,
                          category: {
                            ...fetchMoreResult.category,
                            products: {
                              ...fetchMoreResult.category.products,
                              pageInfo: {
                                ...fetchMoreResult.category.products.pageInfo,
                                hasPreviousPage: true
                              }
                            }
                          }
                        };
                      },
                      variables: {
                        after: category.products.pageInfo.endCursor,
                        first: 12
                      }
                    });
                  };
                  const loadPreviousPage = () => {
                    if (loading) {
                      return;
                    }
                    return fetchMore({
                      updateQuery: (
                        previousResult,
                        { fetchMoreResult, variables }
                      ) => {
                        return {
                          ...fetchMoreResult,
                          category: {
                            ...fetchMoreResult.category,
                            products: {
                              ...fetchMoreResult.category.products,
                              pageInfo: {
                                ...fetchMoreResult.category.products.pageInfo,
                                hasNextPage: true
                              }
                            }
                          }
                        };
                      },
                      variables: {
                        before: category.products.pageInfo.startCursor,
                        first: undefined,
                        last: 12
                      }
                    });
                  };
                  return (
                    <Grid container spacing={16}>
                      <Grid item xs={12}>
                        <Grid container spacing={16}>
                          <Grid item xs={12} md={9}>
                            <CategoryProperties
                              category={category}
                              loading={loading}
                            />
                          </Grid>
                        </Grid>
                      </Grid>
                      <Grid item xs={12}>
                        <Grid container spacing={16}>
                          <Grid item xs={12} md={9}>
                            <NavigatorLink
                              to={category ? categoryAddUrl(category.id) : "#"}
                            >
                              {handleCreate => (
                                <CategorySubcategories
                                  data={data}
                                  loading={loading}
                                  onCreate={handleCreate}
                                />
                              )}
                            </NavigatorLink>
                          </Grid>
                        </Grid>
                      </Grid>
                      <Grid item xs={12}>
                        <Grid container spacing={16}>
                          <Grid item xs={12} md={9}>
                            <CategoryProducts
                              data={data}
                              loading={loading}
                              onCreate={() => undefined}
                              onFilter={this.handleFilterMenuOpen}
                              onNextPage={loadNextPage}
                              onPreviousPage={loadPreviousPage}
                            />
                          </Grid>
                          <Hidden smDown>
                            <Grid item xs={12} md={3}>
                              <ProductFilters
                                handleSubmit={applyFilters}
                                handleClear={clearFilters}
                                productTypes={dummyProductTypes}
                                formState={filters}
                              />
                            </Grid>
                          </Hidden>
                          <Hidden mdUp>
                            <Drawer
                              open={this.state.isFilterMenuOpened}
                              onClose={this.handleFilterMenuOpen}
                              anchor="bottom"
                            >
                              <ProductFilters
                                handleSubmit={applyFilters}
                                handleClear={clearFilters}
                                productTypes={dummyProductTypes}
                                formState={filters}
                              />
                            </Drawer>
                          </Hidden>
                        </Grid>
                      </Grid>
                    </Grid>
                  );
                }}
              </TypedCategoryPropertiesQuery>
            );
          }}
        </Navigator>
      );
    }
    return (
      <TypedRootCategoryChildrenQuery
        query={rootCategoryChildrenQuery}
        fetchPolicy="network-only"
      >
        {({ error, loading, data }) => {
          if (error) {
            return <span>not ok</span>;
          }
          return (
            <Grid container spacing={16}>
              <Grid item xs={12} md={9}>
                <NavigatorLink to={categoryAddUrl()}>
                  {handleCreate => (
                    <RootCategoryList
                      data={data}
                      loading={loading}
                      onCreate={handleCreate}
                    />
                  )}
                </NavigatorLink>
              </Grid>
            </Grid>
          );
        }}
      </TypedRootCategoryChildrenQuery>
    );
  }
}

export default CategoryDetails;
