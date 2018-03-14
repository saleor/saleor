import Button from "material-ui/Button";
import Divider from "material-ui/Divider";
import Grid from "material-ui/Grid";
import IconButton from "material-ui/IconButton";
import Toolbar from "material-ui/Toolbar";
import Typography from "material-ui/Typography";
import { withStyles } from "material-ui/styles";
import ArrowBack from "material-ui-icons/ArrowBack";
import * as React from "react";
import { Link } from "react-router-dom";

import {
  categoryPropertiesQuery,
  TypedCategoryPropertiesQuery,
  rootCategoryChildrenQuery,
  TypedRootCategoryChildrenQuery
} from "../queries";
import CategoryProperties from "../components/CategoryProperties";
import CategoryChildElement from "../components/CategoryChildElement";
import CategoryList from "../components/CategoryList";
import ProductChildElement from "../components/ProductChildElement";
import ProductList from "../components/ProductList";
import { categoryShowUrl, categoryAddUrl } from "../index";
import PageHeader from "../../components/PageHeader";
import Skeleton from "../../components/Skeleton";
import i18n from "../../i18n";

const decorate = withStyles(theme => ({
  grid: {
    padding: theme.spacing.unit * 2
  },
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
              <>
                <PageHeader
                  backLink={
                    category
                      ? categoryShowUrl(category.parent && category.parent.id)
                      : "#"
                  }
                  loading={loading}
                  title={(category && category.name) || ""}
                />
                <Grid container spacing={24} className={classes.grid}>
                  <Grid item xs={12}>
                    <CategoryProperties category={category} loading={loading} />
                  </Grid>
                  <Grid item xs={12}>
                    <div className={classes.subtitle}>
                      <Typography className={classes.title} variant="title">
                        {i18n.t("Subcategories", { context: "title" })}
                      </Typography>
                      <Button
                        color="secondary"
                        component={props => (
                          <Link
                            to={category ? categoryAddUrl(category.id) : "#"}
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
                      categories={
                        category && category.children && category.children.edges
                      }
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <div className={classes.subtitle}>
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
                      products={
                        category && category.products && category.products.edges
                      }
                      handleLoadMore={handleLoadMore}
                      canLoadMore={
                        category &&
                        category.products &&
                        category.products.pageInfo &&
                        category.products.pageInfo.hasNextPage
                      }
                    />
                  </Grid>
                </Grid>
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
              <PageHeader title={i18n.t("Categories", { context: "title" })}>
                <Button
                  color="secondary"
                  component={props => <Link to={categoryAddUrl()} {...props} />}
                  disabled={loading}
                  variant="raised"
                >
                  {i18n.t("Add category", { context: "button" })}
                </Button>
              </PageHeader>
              <div className={classes.grid}>
                <CategoryList categories={categories && categories.edges} />
              </div>
            </>
          );
        }}
      </TypedRootCategoryChildrenQuery>
    );
  }
);

export default CategoryDetails;
