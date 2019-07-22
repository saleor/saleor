import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import AddIcon from "@material-ui/icons/Add";
import React from "react";

import Container from "@saleor/components/Container";
import PageHeader from "@saleor/components/PageHeader";
import ProductList from "@saleor/components/ProductList";
import i18n from "@saleor/i18n";
import {
  FilterPageProps,
  ListActions,
  ListSettings,
  PageListProps
} from "@saleor/types";
import { CategoryDetails_category_products_edges_node } from "../../../categories/types/CategoryDetails";
import { ProductListUrlFilters } from "../../urls";
import ProductListFilter from "../ProductListFilter";

export interface ProductListCardProps
  extends PageListProps,
    ListActions,
    FilterPageProps<ProductListUrlFilters> {
  currencySymbol: string;
  listSettings?: ListSettings;
  products: CategoryDetails_category_products_edges_node[];
}

export const ProductListCard: React.StatelessComponent<
  ProductListCardProps
> = ({
  currencySymbol,
  currentTab,
  filtersList,
  filterTabs,
  initialSearch,
  onAdd,
  onAll,
  onSearchChange,
  onFilterAdd,
  onFilterSave,
  onTabChange,
  onFilterDelete,
  ...listProps
}) => {
  return (
    <Container>
      <PageHeader title={i18n.t("Products")}>
        <Button onClick={onAdd} color="primary" variant="contained">
          {i18n.t("Add product")} <AddIcon />
        </Button>
      </PageHeader>
      <Card>
        <ProductListFilter
          allTabLabel={i18n.t("All Products")}
          currencySymbol={currencySymbol}
          currentTab={currentTab}
          filterLabel={i18n.t("Select all products where:")}
          filterTabs={filterTabs}
          filtersList={filtersList}
          initialSearch={initialSearch}
          searchPlaceholder={i18n.t("Search Products...")}
          onAll={onAll}
          onSearchChange={onSearchChange}
          onFilterAdd={onFilterAdd}
          onFilterSave={onFilterSave}
          onTabChange={onTabChange}
          onFilterDelete={onFilterDelete}
        />
        <ProductList {...listProps} />
      </Card>
    </Container>
  );
};
ProductListCard.displayName = "ProductListCard";
export default ProductListCard;
