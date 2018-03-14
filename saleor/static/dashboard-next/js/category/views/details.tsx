import Button from "material-ui/Button";
import Divider from "material-ui/Divider";
import Grid from "material-ui/Grid";
import IconButton from "material-ui/IconButton";
import Toolbar from "material-ui/Toolbar";
import Typography from "material-ui/Typography";
import { withStyles, WithStyles } from "material-ui/styles";
import ArrowBack from "material-ui-icons/ArrowBack";
import FilterList from "material-ui-icons/FilterList";
import * as React from "react";
import { Component } from "react";
import { Link } from "react-router-dom";
import TextField from "material-ui/TextField";
import Hidden from "material-ui/Hidden";
import Drawer from "material-ui/Drawer";
import AddIcon from "material-ui-icons/Add";

import {
  categoryPropertiesQuery,
  TypedCategoryPropertiesQuery,
  rootCategoryChildrenQuery,
  TypedRootCategoryChildrenQuery
} from "../queries";
import CategoryProperties from "../components/CategoryProperties";
import { CategoryChildElement } from "../components/CategoryChildElement";
import { categoryShowUrl, categoryAddUrl } from "../index";
import { ProductChildElement } from "../components/ProductChildElement";
import { CategoryList } from "../components/CategoryList";
import { ProductList } from "../components/ProductList";
import i18n from "../../i18n";
import { Skeleton } from "../../components/Skeleton";
import { FilterCard } from "../../components/cards";

const decorate = withStyles(theme => ({
  grid: {
    padding: theme.spacing.unit * 2
  },
  menuButton: {
    marginRight: theme.spacing.unit * 2
  },
  title: {
    flex: 1
  },
  toolbar: {
    backgroundColor: theme.palette.background.paper
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
    CategoryDetailsProps &
      WithStyles<"grid" | "menuButton" | "title" | "toolbar" | "subtitle">,
    CategoryDetailsState
  > {
    state = { isFilterMenuOpened: false };

    handleFilterMenuToggle = () => {
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
                <>
                  <Toolbar className={classes.toolbar}>
                    <IconButton
                      color="inherit"
                      className={classes.menuButton}
                      component={props => (
                        <Link
                          to={
                            loading
                              ? ""
                              : categoryShowUrl(
                                  category.parent && category.parent.id
                                )
                          }
                          {...props}
                        />
                      )}
                      disabled={loading}
                    >
                      <ArrowBack />
                    </IconButton>
                    <Typography className={classes.title} variant="title">
                      {loading ? (
                        <Skeleton style={{ width: "10em" }} />
                      ) : (
                        category.name
                      )}
                    </Typography>
                    <Hidden mdUp>
                      <IconButton
                        color="inherit"
                        disabled={loading}
                        onClick={this.handleFilterMenuToggle}
                      >
                        <FilterList />
                      </IconButton>
                    </Hidden>
                  </Toolbar>
                  <Divider />
                  <Grid container spacing={0}>
                    <Grid item xs={12} md={9}>
                      <Grid container spacing={24} className={classes.grid}>
                        <Grid item xs={12}>
                          <CategoryProperties
                            category={category}
                            loading={loading}
                          />
                        </Grid>
                        <Grid item xs={12}>
                          <div className={classes.subtitle}>
                            <Typography
                              className={classes.title}
                              variant="title"
                            >
                              {i18n.t("Subcategories", { context: "title" })}
                            </Typography>
                            <IconButton
                              color="inherit"
                              component={props => (
                                <Link
                                  to={
                                    loading ? "" : categoryAddUrl(category.id)
                                  }
                                  {...props}
                                />
                              )}
                              disabled={loading}
                            >
                              <AddIcon />
                            </IconButton>
                          </div>
                          <CategoryList
                            loading={loading}
                            categories={loading ? [] : category.children.edges}
                          />
                        </Grid>
                        <Grid item xs={12}>
                          <div className={classes.subtitle}>
                            <Typography
                              className={classes.title}
                              variant="title"
                            >
                              {i18n.t("Products", { context: "title" })}
                            </Typography>
                            <IconButton
                              color="inherit"
                              component={props => <Link to="#" {...props} />}
                              disabled={loading}
                            >
                              <AddIcon />
                            </IconButton>
                          </div>
                          <ProductList
                            loading={loading}
                            products={loading ? [] : category.products.edges}
                            handleLoadMore={handleLoadMore}
                            canLoadMore={
                              loading
                                ? false
                                : category.products.pageInfo.hasNextPage
                            }
                          />
                        </Grid>
                      </Grid>
                    </Grid>
                    <Hidden smDown>
                      <Grid item xs={12} md={3}>
                        <Grid container spacing={24} className={classes.grid}>
                          <Grid item xs={12}>
                            <FilterCard
                              handleSubmit={() => {}}
                              handleClear={() => {}}
                            >
                              <TextField fullWidth />
                            </FilterCard>
                          </Grid>
                        </Grid>
                      </Grid>
                    </Hidden>
                  </Grid>
                  <Drawer
                    anchor="bottom"
                    open={this.state.isFilterMenuOpened}
                    onClose={this.handleFilterMenuToggle}
                  >
                    <FilterCard handleClear={() => {}} handleSubmit={() => {}}>
                      <TextField fullWidth />
                    </FilterCard>
                  </Drawer>
                </>
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
              <>
                <Toolbar className={classes.toolbar}>
                  <Typography className={classes.title} variant="title">
                    {i18n.t("Categories", { context: "title" })}
                  </Typography>
                  <IconButton
                    color="inherit"
                    component={props => (
                      <Link to={categoryAddUrl()} {...props} />
                    )}
                    disabled={loading}
                  >
                    <AddIcon />
                  </IconButton>
                  <Hidden mdUp>
                    <IconButton
                      color="inherit"
                      disabled={loading}
                      onClick={this.handleFilterMenuToggle}
                    >
                      <FilterList />
                    </IconButton>
                  </Hidden>
                </Toolbar>
                <Divider />
                <Grid container spacing={24} className={classes.grid}>
                  <Grid item xs={12} md={9}>
                    <CategoryList
                      loading={loading}
                      categories={loading ? [] : categories.edges}
                    />
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <Hidden smDown>
                      <FilterCard
                        handleClear={() => {}}
                        handleSubmit={() => {}}
                      >
                        <TextField fullWidth />
                      </FilterCard>
                    </Hidden>
                  </Grid>
                </Grid>
                <Drawer
                  anchor="bottom"
                  open={this.state.isFilterMenuOpened}
                  onClose={this.handleFilterMenuToggle}
                >
                  <FilterCard handleClear={() => {}} handleSubmit={() => {}}>
                    <TextField fullWidth />
                  </FilterCard>
                </Drawer>
              </>
            );
          }}
        </TypedRootCategoryChildrenQuery>
      );
    }
  }
);

export default CategoryDetails;
