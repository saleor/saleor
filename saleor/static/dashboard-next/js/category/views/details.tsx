import Grid from "material-ui/Grid";
import * as React from "react";

import {
  categoryProperties,
  TypedCategoryPropertiesQuery,
  rootCategoryChildren,
  TypedRootCategoryChildrenQuery
} from "../queries";
import CategoryProperties from "../components/CategoryProperties";
import Typography from "material-ui/Typography";
import { pgettext } from "../../i18n";
import { CategoryChildElement } from "../components/CategoryChildElement";
import { categoryShowUrl } from "../index";
import { ProductChildElement } from "../components/ProductChildElement";
import { CategoryList } from "../components/CategoryList";
import { ProductList } from "../components/ProductList";

interface CategoryDetailsProps {
  filters: any;
  id: string;
}

// TODO: Plug-in filters
const CategoryDetails: React.StatelessComponent<CategoryDetailsProps> = ({
  filters,
  id
}) => (
  <Grid container spacing={24}>
    <Grid item xs={12} md={9}>
      {id ? (
        <TypedCategoryPropertiesQuery
          query={categoryProperties}
          variables={{ id, first: 5 }}
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
                <CategoryProperties category={category} loading={loading} />
                <CategoryList
                  loading={loading}
                  categories={loading ? [] : category.children.edges}
                  label={pgettext(
                    "Dashboard category view subcategories section",
                    "Subcategories"
                  )}
                  parentId={loading ? "" : category.id}
                />
                <ProductList
                  loading={loading}
                  products={loading ? [] : category.products.edges}
                  parentId={loading ? "" : category.id}
                  handleLoadMore={handleLoadMore}
                  canLoadMore={
                    loading ? false : category.products.pageInfo.hasNextPage
                  }
                />
              </>
            );
          }}
        </TypedCategoryPropertiesQuery>
      ) : (
        <TypedRootCategoryChildrenQuery
          query={rootCategoryChildren}
          fetchPolicy="network-only"
        >
          {({ error, loading, data: { categories } }) => {
            if (error) {
              return <span>not ok</span>;
            }
            return (
              <CategoryList
                loading={loading}
                categories={loading ? [] : categories.edges}
                label={pgettext(
                  "Dashboard category view subcategories section",
                  "Subcategories"
                )}
                parentId=""
              />
            );
          }}
        </TypedRootCategoryChildrenQuery>
      )}
    </Grid>
  </Grid>
);

export default CategoryDetails;
