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
import CategoryList from "../components/CategoryList";
import CategoryProperties from "../components/CategoryProperties";
import ProductFilters from "../components/ProductFilters";
import ProductList from "../components/ProductList";
import RootCategoryList from "../components/RootCategoryList";
import { categoryAddUrl } from "../index";
import {
  categoryPropertiesQuery,
  rootCategoryChildrenQuery,
  TypedCategoryPropertiesQuery,
  TypedRootCategoryChildrenQuery
} from "../queries";

const { Component } = React;

const decorate = withStyles(theme => ({
  subtitle: {
    alignItems: "center" as "center",
    display: "flex",
    marginBottom: theme.spacing.unit * 2
  },
  title: {
    flex: 1
  }
}));

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

const CategoryDetails = decorate(
  class CategoryDetailsComponent extends Component<
    CategoryDetailsProps & WithStyles<"title" | "subtitle">,
    CategoryDetailsState
  > {
    state = { isFilterMenuOpened: false };

    handleFilterMenuOpen = () => {
      this.setState(prevState => ({
        isFilterMenuOpened: !prevState.isFilterMenuOpened
      }));
    };

    render() {
      const { classes, filters, id } = this.props;
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
                              <Card>
                                <PageHeader
                                  title={i18n.t("Subcategories", {
                                    context: "title"
                                  })}
                                >
                                  <IconButton
                                    component={props => (
                                      <Link
                                        to={
                                          category
                                            ? categoryAddUrl(category.id)
                                            : "#"
                                        }
                                        {...props}
                                      />
                                    )}
                                    disabled={loading}
                                  >
                                    <AddIcon />
                                  </IconButton>
                                </PageHeader>
                                <CategoryList
                                  categories={
                                    category &&
                                    category.children &&
                                    category.children.edges
                                  }
                                />
                              </Card>
                            </Grid>
                          </Grid>
                        </Grid>
                        <Grid item xs={12}>
                          <Grid container spacing={16}>
                            <Grid item xs={12} md={9}>
                              <Card>
                                <PageHeader
                                  title={i18n.t("Products", {
                                    context: "title"
                                  })}
                                >
                                  <IconButton
                                    component={props => (
                                      <Link to="#" {...props} />
                                    )}
                                    disabled={loading}
                                  >
                                    <AddIcon />
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
                                <ProductList
                                  hasNextPage={
                                    category &&
                                    category.products &&
                                    category.products.pageInfo &&
                                    category.products.pageInfo.hasNextPage
                                  }
                                  hasPreviousPage={
                                    category &&
                                    category.products &&
                                    category.products.pageInfo &&
                                    category.products.pageInfo.hasPreviousPage
                                  }
                                  onNextPage={loadNextPage}
                                  onPreviousPage={loadPreviousPage}
                                  products={
                                    category &&
                                    category.products &&
                                    category.products.edges
                                  }
                                />
                              </Card>
                            </Grid>
                            <Grid item xs={12} md={3}>
                              <Hidden smDown>
                                <ProductFilters
                                  handleSubmit={applyFilters}
                                  handleClear={clearFilters}
                                  productTypes={dummyProductTypes}
                                  formState={filters}
                                />
                              </Hidden>
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
                            </Grid>
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
);

export default CategoryDetails;
