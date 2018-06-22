import * as React from "react";
import { Redirect } from "react-router-dom";

import CategoryDetailsPage from "../../categories/components/CategoryDetailsPage";
import ErrorMessageCard from "../../components/ErrorMessageCard";
import Navigator from "../../components/Navigator";
import { CategoryPropertiesQuery } from "../../gql-types";
import i18n from "../../i18n";
import { productAddUrl, productUrl } from "../../products";
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
    {(deleteCategory, { called, loading, error: deleteError }) => {
      if (called && !loading) {
        return (
          <Redirect
            to={categoryShowUrl(category.parent ? category.parent.id : null)}
            push={false}
          />
        );
      }
      if (deleteError) {
        return <ErrorMessageCard message={deleteError.message} />;
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
          <ErrorMessageCard
            message={i18n.t("Unable to find a matching category.")}
          />
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

const CategoryDetails: React.StatelessComponent<CategoryDetailsProps> = ({
  filters,
  id
}) => {
  if (id) {
    return (
      <Navigator>
        {navigate => {
          return (
            <CategoryPaginationProvider id={id}>
              {({ data, loading, fetchNextPage, fetchPreviousPage }) => {
                return (
                  <CategoryDeleteProvider category={data.category}>
                    {deleteCategory => (
                      <CategoryDetailsPage
                        category={data ? data.category : undefined}
                        products={
                          data && data.category && data.category.products
                            ? data.category.products.edges.map(
                                edge => edge.node
                              )
                            : undefined
                        }
                        subcategories={
                          data && data.category && data.category.children
                            ? data.category.children.edges.map(
                                edge => edge.node
                              )
                            : undefined
                        }
                        loading={loading}
                        onAddCategory={() => navigate(categoryAddUrl(id))}
                        onAddProduct={() => navigate(productAddUrl)}
                        onBack={() => window.history.back()}
                        onCategoryClick={(id: string) => () =>
                          navigate(categoryShowUrl(id))}
                        onDelete={deleteCategory}
                        onEdit={() => navigate(categoryEditUrl(id))}
                        onProductClick={(id: string) => () =>
                          navigate(productUrl(id))}
                        pageInfo={
                          data && data.category && data.category.products
                            ? data.category.products.pageInfo
                            : undefined
                        }
                        onNextPage={fetchNextPage}
                        onPreviousPage={fetchPreviousPage}
                      />
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
          return <ErrorMessageCard message={error.message} />;
        }
        return (
          <Navigator>
            {navigate => (
              <CategoryDetailsPage
                subcategories={
                  data && data.categories
                    ? data.categories.edges.map(edge => edge.node)
                    : undefined
                }
                loading={loading}
                onAddCategory={() => navigate(categoryAddUrl())}
                onAddProduct={() => navigate(productAddUrl)}
                onBack={() => window.history.back()}
                onCategoryClick={(id: string) => () =>
                  navigate(categoryShowUrl(id))}
                onProductClick={(id: string) => () =>
                  navigate(productUrl(id))}
              />
            )}
          </Navigator>
        );
      }}
    </TypedRootCategoryChildrenQuery>
  );
};

export default CategoryDetails;
