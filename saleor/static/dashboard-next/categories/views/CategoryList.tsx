import * as React from "react";

import { categoryAddUrl, categoryUrl } from "..";
import Navigator from "../../components/Navigator";
import { maybe } from "../../misc";
import { CategoryListPage } from "../components/CategoryListPage/CategoryListPage";
import { TypedRootCategoriesQuery } from "../queries";

export const CategoryList: React.StatelessComponent = () => (
  <Navigator>
    {navigate => (
      <TypedRootCategoriesQuery>
        {({ data }) => (
          <CategoryListPage
            categories={maybe(
              () => data.categories.edges.map(edge => edge.node),
              []
            )}
            onAddCategory={() => navigate(categoryAddUrl())}
            onCategoryClick={id => () =>
              navigate(categoryUrl(encodeURIComponent(id)))}
          />
        )}
      </TypedRootCategoriesQuery>
    )}
  </Navigator>
);
export default CategoryList;
