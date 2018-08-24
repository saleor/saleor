import * as React from "react";
import { Redirect } from "react-router-dom";

import CategoryDetailsPage from "../../categories/components/CategoryDetailsPage";
import ErrorMessageCard from "../../components/ErrorMessageCard";
import Navigator from "../../components/Navigator";
import { CategoryPropertiesQuery } from "../../gql-types";
import i18n from "../../i18n";
import {
  createPaginationData,
  createPaginationState,
  PageInfo
} from "../../misc";
import { productAddUrl, productUrl } from "../../products";
import { categoryAddUrl, categoryEditUrl, categoryShowUrl } from "../index";
import {
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

interface QueryParams {
  after?: string;
  before?: string;
}

const PAGINATE_BY = 20;

const CategoryDeleteProvider: React.StatelessComponent<
  CategoryDeleteProviderProps
> = ({ category, children }) => (
  <TypedCategoryDeleteMutation
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
        return children(deleteCategory);
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
          pageInfo: PageInfo;
          loadNextPage: () => void;
          loadPreviousPage: () => void;
        }
      ) => React.ReactElement<any>)
    | React.ReactNode;
  id?: string;
  navigate: (url: string, push: boolean) => void;
  params: QueryParams;
}

const CategoryPaginationProvider: React.StatelessComponent<
  CategoryPaginationProviderProps
> = ({ children, id, navigate, params }) => {
  const paginationState = createPaginationState(PAGINATE_BY, params);
  return (
    <TypedCategoryPropertiesQuery
      query={categoryPropertiesQuery}
      variables={{ id, ...paginationState }}
      fetchPolicy="network-only"
    >
      {({ loading, error, data }) => {
        if (error) {
          return (
            <ErrorMessageCard
              message={i18n.t("Unable to find a matching category.")}
            />
          );
        }
        const {
          loadNextPage,
          loadPreviousPage,
          pageInfo
        } = createPaginationData(
          navigate,
          paginationState,
          categoryShowUrl(id),
          data && data.category && data.category.products
            ? data.category.products.pageInfo
            : undefined,
          loading
        );

        if (typeof children === "function") {
          return children({
            data,
            loadNextPage,
            loadPreviousPage,
            loading,
            pageInfo
          });
        }
        if (React.Children.count(children) > 0) {
          return React.Children.only(children);
        }
        return null;
      }}
    </TypedCategoryPropertiesQuery>
  );
};

interface CategoryDetailsProps {
  params: QueryParams;
  id: string;
}

const CategoryDetails: React.StatelessComponent<CategoryDetailsProps> = ({
  params,
  id
}) => {
  if (id) {
    return (
      <Navigator>
        {navigate => {
          return (
            <CategoryPaginationProvider
              id={id}
              params={params}
              navigate={navigate}
            >
              {({
                data,
                loading,
                loadNextPage,
                loadPreviousPage,
                pageInfo
              }) => {
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
                        onCategoryClick={id => () =>
                          navigate(categoryShowUrl(id))}
                        onDelete={deleteCategory}
                        onEdit={() => navigate(categoryEditUrl(id))}
                        onProductClick={id => () => navigate(productUrl(id))}
                        pageInfo={pageInfo}
                        onNextPage={loadNextPage}
                        onPreviousPage={loadPreviousPage}
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
                onCategoryClick={id => () => navigate(categoryShowUrl(id))}
                onProductClick={id => () => navigate(productUrl(id))}
              />
            )}
          </Navigator>
        );
      }}
    </TypedRootCategoryChildrenQuery>
  );
};

export default CategoryDetails;
