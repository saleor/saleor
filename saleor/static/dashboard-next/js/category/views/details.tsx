import Button from "material-ui/Button";
import Grid from "material-ui/Grid";
import Typography from "material-ui/Typography";
import { withStyles } from "material-ui/styles";
import * as React from "react";

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
import { Link } from "react-router-dom";

const decorate = withStyles(theme => ({
  toolbar: {
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

// TODO: Plug-in filters
const CategoryDetails = decorate<CategoryDetailsProps>(
  ({ classes, filters, id }) => {
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
                  <CategoryProperties category={category} loading={loading} />
                </Grid>
                <Grid item xs={12}>
                  <div className={classes.toolbar}>
                    <Typography className={classes.title} variant="title">
                      {i18n.t("Subcategories", { context: "title" })}
                    </Typography>
                    <Button
                      color="secondary"
                      component={props => (
                        <Link
                          to={loading ? "" : categoryAddUrl(category.id)}
                          {...props}
                        />
                      )}
                      disabled={loading}
                      variant="raised"
                    >
                      {i18n.t("Add category", { context: "button" })}
                    </Button>
                  </div>
                  <CategoryList
                    loading={loading}
                    categories={loading ? [] : category.children.edges}
                  />
                </Grid>
                <Grid item xs={12}>
                  <div className={classes.toolbar}>
                    <Typography className={classes.title} variant="title">
                      {i18n.t("Products", { context: "title" })}
                    </Typography>
                    <Button
                      color="secondary"
                      component={props => <Link to="#" {...props} />}
                      disabled={loading}
                      variant="raised"
                    >
                      {i18n.t("Add product", { context: "button" })}
                    </Button>
                  </div>
                  <ProductList
                    loading={loading}
                    products={loading ? [] : category.products.edges}
                    parentId={loading ? "" : category.id}
                    handleLoadMore={handleLoadMore}
                    canLoadMore={
                      loading ? false : category.products.pageInfo.hasNextPage
                    }
                  />
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
            <>
              <div className={classes.toolbar}>
                <Typography className={classes.title} variant="title">
                  {i18n.t("Categories", { context: "title" })}
                </Typography>
                <Button
                  color="secondary"
                  component={props => <Link to={categoryAddUrl()} {...props} />}
                  disabled={loading}
                  variant="raised"
                >
                  {i18n.t("Add category", { context: "button" })}
                </Button>
              </div>
              <CategoryList
                loading={loading}
                categories={loading ? [] : categories.edges}
              />
            </>
          );
        }}
      </TypedRootCategoryChildrenQuery>
    );
  }
);

export default CategoryDetails;
