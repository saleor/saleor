import AddIcon from "material-ui-icons/Add";
import FilterListIcon from "material-ui-icons/FilterList";
import Card from "material-ui/Card";
import Hidden from "material-ui/Hidden";
import IconButton from "material-ui/IconButton";
import * as React from "react";

import PageHeader from "../../../components/PageHeader";
import ProductList from "../../../components/ProductList";
import i18n from "../../../i18n";

interface CategoryProductsProps {
  hasPreviousPage: boolean;
  hasNextPage: boolean;
  products?: Array<{
    id: string;
    name: string;
    thumbnailUrl: string;
    productType: {
      id: string;
      name: string;
    };
  }>;
  onCreate?();
  onFilter?();
  onNextPage?();
  onPreviousPage?();
}

const CategoryProducts: React.StatelessComponent<CategoryProductsProps> = ({
  hasNextPage,
  hasPreviousPage,
  onCreate,
  onFilter,
  onNextPage,
  onPreviousPage,
  products
}) => (
  <Card>
    <PageHeader
      title={i18n.t("Products", {
        context: "title"
      })}
    >
      <IconButton onClick={onCreate}>
        <AddIcon />
      </IconButton>
      <Hidden mdUp>
        <IconButton onClick={onFilter}>
          <FilterListIcon />
        </IconButton>
      </Hidden>
    </PageHeader>
    <ProductList
      hasNextPage={hasNextPage}
      hasPreviousPage={hasPreviousPage}
      onNextPage={onNextPage}
      onPreviousPage={onPreviousPage}
      products={products}
    />
  </Card>
);

export default CategoryProducts;
