import AddIcon from "material-ui-icons/Add";
import FilterListIcon from "material-ui-icons/FilterList";
import Card from "material-ui/Card";
import Hidden from "material-ui/Hidden";
import IconButton from "material-ui/IconButton";
import * as React from "react";

import PageHeader from "../../components/PageHeader";
import ProductList from "../../components/ProductList";
import { CategoryPropertiesQuery } from "../../gql-types";
import i18n from "../../i18n";

interface CategoryProductsProps {
  data: CategoryPropertiesQuery;
  loading?: boolean;
  onCreate?();
  onFilter?();
  onNextPage?();
  onPreviousPage?();
}

const CategoryProducts: React.StatelessComponent<CategoryProductsProps> = ({
  data,
  loading,
  onCreate,
  onFilter,
  onNextPage,
  onPreviousPage
}) => (
  <Card>
    <PageHeader
      title={i18n.t("Products", {
        context: "title"
      })}
    >
      <IconButton disabled={loading} onClick={onCreate}>
        <AddIcon />
      </IconButton>
      <Hidden mdUp>
        <IconButton disabled={loading} onClick={onFilter}>
          <FilterListIcon />
        </IconButton>
      </Hidden>
    </PageHeader>
    <ProductList
      hasNextPage={
        data.category &&
        data.category.products &&
        data.category.products.pageInfo &&
        data.category.products.pageInfo.hasNextPage
      }
      hasPreviousPage={
        data.category &&
        data.category.products &&
        data.category.products.pageInfo &&
        data.category.products.pageInfo.hasPreviousPage
      }
      onNextPage={onNextPage}
      onPreviousPage={onPreviousPage}
      products={
        data.category &&
        data.category.products &&
        data.category.products.edges.map(edge => edge.node)
      }
    />
  </Card>
);

export default CategoryProducts;
