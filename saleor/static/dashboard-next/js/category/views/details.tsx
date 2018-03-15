import Button from "material-ui/Button";
import Divider from "material-ui/Divider";
import Grid from "material-ui/Grid";
import IconButton from "material-ui/IconButton";
import Toolbar from "material-ui/Toolbar";
import Typography from "material-ui/Typography";
import { withStyles, WithStyles } from "material-ui/styles";
import ArrowBack from "material-ui-icons/ArrowBack";
import Add from "material-ui-icons/Add";
import * as React from "react";
import { Link } from "react-router-dom";
import { Component } from "react";
import Card from "material-ui/Card";
import FilterListIcon from "material-ui-icons/FilterList";
import Drawer from "material-ui/Drawer";

import {
  categoryPropertiesQuery,
  TypedCategoryPropertiesQuery,
  rootCategoryChildrenQuery,
  TypedRootCategoryChildrenQuery
} from "../queries";
import CategoryProperties from "../components/CategoryProperties";
import CategoryList from "../components/CategoryList";
import ProductList from "../components/ProductList";
import { categoryShowUrl, categoryAddUrl } from "../index";
import PageHeader from "../../components/PageHeader";
import Skeleton from "../../components/Skeleton";
import i18n from "../../i18n";
import Hidden from "material-ui/Hidden";
import FilterCard from "../../components/cards/FilterCard";
import { ProductFilters } from "../components/ProductFilters";

const decorate = withStyles(theme => ({
  title: {
    flex: 1
  },
  subtitle: {
    display: "flex",
    alignItems: "center" as "center",
    marginBottom: theme.spacing.unit * 2
  }
}));

interface CategoryDetailsProps {
  filters: any;
  id: string;
}
interface CategoryDetailsState {
  isFilterMenuOpened: boolean;
}

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
          <TypedCategoryPropertiesQuery
            query={categoryPropertiesQuery}
            variables={{ id, first: 12 }}
            fetchPolicy="network-only"
          >
            {({ loading, error, data: { category }, fetchMore }) => {
              if (error) {
                return <span>not ok</span>;
              }
              const handleLoadMore = () => {
                if (loading) {
                  return;
                }
                return fetchMore({
                  variables: {
                    after: category.products.pageInfo.endCursor
                  },
                  updateQuery: (previousResult, { fetchMoreResult }) => {
                    return {
                      ...previousResult,
                      category: {
                        ...previousResult.category,
                        products: {
                          ...previousResult.category.products,
                          edges: [
                            ...previousResult.category.products.edges,
                            ...fetchMoreResult.category.products.edges
                          ],
                          pageInfo: {
                            ...fetchMoreResult.category.products.pageInfo
                          }
                        }
                      }
                    };
                  }
                });
              };
              return (
                <Grid container spacing={24}>
                  <Grid item xs={12}>
                    <Grid container spacing={24}>
                      <Grid item xs={12} md={9}>
                        <CategoryProperties
                          category={category}
                          loading={loading}
                        />
                      </Grid>
                    </Grid>
                  </Grid>
                  <Grid item xs={12}>
                    <Grid container spacing={24}>
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
                                    category ? categoryAddUrl(category.id) : "#"
                                  }
                                  {...props}
                                />
                              )}
                              disabled={loading}
                            >
                              <Add />
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
                    <Grid container spacing={24}>
                      <Grid item xs={12} md={9}>
                        <Card>
                          <PageHeader
                            title={i18n.t("Products", { context: "title" })}
                          >
                            <IconButton
                              component={props => <Link to="#" {...props} />}
                              disabled={loading}
                            >
                              <Add />
                            </IconButton>
                            <Hidden mdUp implementation="css">
                              <IconButton
                                disabled={loading}
                                onClick={this.handleFilterMenuOpen}
                              >
                                <FilterListIcon />
                              </IconButton>
                            </Hidden>
                          </PageHeader>
                          <ProductList
                            products={
                              category &&
                              category.products &&
                              category.products.edges
                            }
                            handleLoadMore={handleLoadMore}
                            canLoadMore={
                              category &&
                              category.products &&
                              category.products.pageInfo &&
                              category.products.pageInfo.hasNextPage
                            }
                          />
                        </Card>
                      </Grid>
                      <Grid item xs={12} md={3}>
                        <Hidden smDown implementation="css">
                          <ProductFilters
                            handleClear={() => {}}
                            handleSubmit={() => {}}
                          />
                        </Hidden>
                        <Drawer
                          open={this.state.isFilterMenuOpened}
                          onClose={this.handleFilterMenuOpen}
                          anchor="bottom"
                        >
                          <ProductFilters
                            handleClear={() => {}}
                            handleSubmit={() => {}}
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
      }
      return (
        <TypedRootCategoryChildrenQuery
          query={rootCategoryChildrenQuery}
          fetchPolicy="network-only"
        >
          {({ error, loading, data: { categories } }) => {
            if (error) {
              return <span>not ok</span>;
            }
            return (
              <Card>
                <PageHeader title={i18n.t("Categories", { context: "title" })}>
                  <IconButton
                    component={props => (
                      <Link to={categoryAddUrl()} {...props} />
                    )}
                    disabled={loading}
                  >
                    <Add />
                  </IconButton>
                </PageHeader>
                <CategoryList categories={categories && categories.edges} />
              </Card>
            );
          }}
        </TypedRootCategoryChildrenQuery>
      );
    }
  }
);

export default CategoryDetails;
