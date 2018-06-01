import Drawer from "material-ui/Drawer";
import Grid from "material-ui/Grid";
import Hidden from "material-ui/Hidden";
import { withStyles } from "material-ui/styles";
import { stringify as stringifyQs } from "qs";
import * as React from "react";
import { Redirect } from "react-router-dom";

import CategoryDeleteDialog from "../../components/CategoryDeleteDialog";
import CategoryPropertiesCard from "../../components/CategoryPropertiesCard";
import ErrorMessageCard from "../../components/ErrorMessageCard";
import Navigator, { NavigatorLink } from "../../components/Navigator";
import Toggle from "../../components/Toggle";
import { CategoryPropertiesQuery } from "../../gql-types";
import { productShowUrl } from "../../products";
import CategoryProducts from "../components/CategoryProducts";
import CategorySubcategories from "../components/CategorySubcategories";
import ProductFilters from "../components/ProductFilters";
import RootCategoryList from "../components/RootCategoryList";
import { categoryAddUrl, categoryEditUrl, categoryShowUrl } from "../index";
import {
  categoryDeleteMutation,
  TypedCategoryDeleteMutation
} from "../mutations";
import {
  categoryPropertiesQuery,
  rootCategoryChildrenQuery,
  TypedCategoryPropertiesQuery,
  TypedRootCategoryChildrenQuery
} from "../queries";

const decorate = withStyles(theme => ({
  root: {
    display: "grid",
    gridGap: theme.spacing.unit + "px",
    gridTemplateColumns: "100%",
    [theme.breakpoints.up("md")]: {
      gridGap: theme.spacing.unit * 2 + "px",
      gridTemplateColumns: "3fr 1fr"
    }
  }
}));

interface CategoryDeleteProviderProps {
  category?: CategoryPropertiesQuery["category"];
  children:
    | ((deleteCategory: () => void) => React.ReactElement<any>)
    | React.ReactNode;
}

const CategoryDeleteProvider: React.StatelessComponent<
  CategoryDeleteProviderProps
> = ({ category, children }) => (
  <TypedCategoryDeleteMutation
    mutation={categoryDeleteMutation}
    variables={{
      id: (category && category.id) || ""
    }}
  >
    {(deleteCategory, { called, loading }) => {
      if (called && !loading) {
        return (
          <Redirect
            to={categoryShowUrl(category.parent ? category.parent.id : null)}
            push={false}
          />
        );
      }

      if (typeof children === "function") {
        return children(() => deleteCategory());
      }
      if (React.Children.count(children) > 0) {
        return React.Children.only(children);
      }
      return null;
    }}
  </TypedCategoryDeleteMutation>
);

interface CategoryPaginationProviderProps {
  children:
    | ((
        props: {
          data: CategoryPropertiesQuery;
          loading: boolean;
          fetchNextPage();
          fetchPreviousPage();
        }
      ) => React.ReactElement<any>)
    | React.ReactNode;
  id?: string;
}

const CategoryPaginationProvider: React.StatelessComponent<
  CategoryPaginationProviderProps
> = ({ children, id }) => (
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
      const updatePageInfo = (
        results: CategoryPropertiesQuery,
        overrides: Partial<
          CategoryPropertiesQuery["category"]["products"]["pageInfo"]
        >
      ) => ({
        ...results,
        category: {
          ...results.category,
          products: {
            ...results.category.products,
            pageInfo: {
              ...results.category.products.pageInfo,
              ...overrides
            }
          }
        }
      });
      const fetchNextPage = () => {
        return fetchMore({
          updateQuery: (previousResult, { fetchMoreResult }) =>
            updatePageInfo(fetchMoreResult, {
              hasPreviousPage: true
            }),
          variables: {
            after: category.products.pageInfo.endCursor,
            first: 12
          }
        });
      };
      const fetchPreviousPage = () => {
        return fetchMore({
          updateQuery: (previousResult, { fetchMoreResult }) =>
            updatePageInfo(fetchMoreResult, {
              hasNextPage: true
            }),
          variables: {
            before: category.products.pageInfo.startCursor,
            first: undefined,
            last: 12
          }
        });
      };
      if (typeof children === "function") {
        return children({ data, loading, fetchNextPage, fetchPreviousPage });
      }
      if (React.Children.count(children) > 0) {
        return React.Children.only(children);
      }
      return null;
    }}
  </TypedCategoryPropertiesQuery>
);

interface CategoryDetailsProps {
  filters: any;
  id: string;
}

// TODO: Replace when API is ready
const dummyProductTypes = [
  { id: "123123123", name: "Type 1" },
  { id: "123123124", name: "Type 2" },
  { id: "123123125", name: "Type 3" },
  { id: "123123126", name: "Type 4" }
];

const CategoryDetails = decorate<CategoryDetailsProps>(
  ({ classes, filters, id }) => {
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
              <CategoryPaginationProvider id={id}>
                {({ data, loading, fetchNextPage, fetchPreviousPage }) => {
                  const dataHasProducts =
                    data && data.category && data.category.products;
                  return (
                    <CategoryDeleteProvider category={data.category}>
                      {deleteCategory => (
                        <Toggle>
                          {(
                            filtersVisible,
                            { disable: hideFilters, enable: showFilters }
                          ) => (
                            <div className={classes.root}>
                              <Toggle>
                                {(
                                  deleteVisible,
                                  { disable: hideDelete, enable: showDelete }
                                ) => (
                                  <NavigatorLink
                                    to={
                                      (data.category &&
                                        categoryShowUrl(
                                          data.category.parent &&
                                            data.category.parent.id
                                        )) ||
                                      "#"
                                    }
                                  >
                                    {handleBack => (
                                      <NavigatorLink
                                        to={
                                          data.category &&
                                          categoryEditUrl(data.category.id)
                                        }
                                      >
                                        {handleEdit => (
                                          <>
                                            <CategoryPropertiesCard
                                              description={
                                                data.category &&
                                                data.category.description
                                              }
                                              onBack={handleBack}
                                              onDelete={showDelete}
                                              onEdit={handleEdit}
                                              title={
                                                data.category &&
                                                data.category.name
                                              }
                                            />
                                            <CategoryDeleteDialog
                                              name={
                                                data.category &&
                                                data.category.name
                                              }
                                              onClose={hideDelete}
                                              onConfirm={deleteCategory}
                                              open={deleteVisible}
                                              productCount={
                                                dataHasProducts &&
                                                data.category.products
                                                  .totalCount
                                              }
                                            />
                                          </>
                                        )}
                                      </NavigatorLink>
                                    )}
                                  </NavigatorLink>
                                )}
                              </Toggle>
                              <Hidden smDown implementation="css" />
                              <NavigatorLink
                                to={
                                  data.category
                                    ? categoryAddUrl(data.category.id)
                                    : "#"
                                }
                              >
                                {handleCreate => (
                                  <CategorySubcategories
                                    subcategories={
                                      data && data.category
                                        ? data.category.children.edges.map(
                                            edge => edge.node
                                          )
                                        : []
                                    }
                                    onClickSubcategory={id =>
                                      navigate(categoryShowUrl(id))
                                    }
                                    onCreate={handleCreate}
                                  />
                                )}
                              </NavigatorLink>
                              <Hidden smDown implementation="css" />
                              <div>
                                {/* CSS grid will make this full height */}
                                <CategoryProducts
                                  products={
                                    dataHasProducts
                                      ? data.category.products.edges.map(
                                          edge => edge.node
                                        )
                                      : []
                                  }
                                  hasPreviousPage={
                                    dataHasProducts
                                      ? data.category.products.pageInfo
                                          .hasPreviousPage
                                      : false
                                  }
                                  hasNextPage={
                                    dataHasProducts
                                      ? data.category.products.pageInfo
                                          .hasNextPage
                                      : false
                                  }
                                  onCreate={() => undefined}
                                  onFilter={showFilters}
                                  onNextPage={fetchNextPage}
                                  onPreviousPage={fetchPreviousPage}
                                />
                              </div>
                              <Hidden smDown implementation="css">
                                <ProductFilters
                                  handleSubmit={applyFilters}
                                  handleClear={clearFilters}
                                  productTypes={dummyProductTypes}
                                  formState={filters}
                                />
                              </Hidden>
                              <Hidden mdUp implementation="css">
                                <Drawer
                                  open={filtersVisible}
                                  onClose={hideFilters}
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
                            </div>
                          )}
                        </Toggle>
                      )}
                    </CategoryDeleteProvider>
                  );
                }}
              </CategoryPaginationProvider>
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
                <Navigator>
                  {navigate => (
                    <NavigatorLink to={categoryAddUrl()}>
                      {handleCreate => (
                        <RootCategoryList
                          categories={
                            data && data.categories
                              ? data.categories.edges.map(edge => edge.node)
                              : []
                          }
                          onClick={id => navigate(categoryShowUrl(id))}
                          onCreate={handleCreate}
                        />
                      )}
                    </NavigatorLink>
                  )}
                </Navigator>
              </Grid>
            </Grid>
          );
        }}
      </TypedRootCategoryChildrenQuery>
    );
  }
);

export default CategoryDetails;
