import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import { CategoryDetails_category_products_edges_node } from "../../../categories/types/CategoryDetails";
import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import ProductList from "../../../components/ProductList";
import { Filter } from "../../../components/TableFilter";
import i18n from "../../../i18n";
import { ListActions, PageListProps } from "../../../types";
import ProductListFilter, { ProductListFilterTabs } from "../ProductListFilter";

interface ProductListCardProps extends PageListProps, ListActions {
  currentTab: ProductListFilterTabs;
  filtersList: Filter[];
  products: CategoryDetails_category_products_edges_node[];
  onAllProducts: () => void;
  onAvailable: () => void;
  onCustomFilter: () => void;
  onOfStock: () => void;
}

export const ProductListCard: React.StatelessComponent<
  ProductListCardProps
> = ({
  currentTab,
  disabled,
  filtersList,
  pageInfo,
  products,
  onAdd,
  onAllProducts,
  onAvailable,
  onCustomFilter,
  onNextPage,
  onOfStock,
  onPreviousPage,
  onRowClick,
  isChecked,
  selected,
  toggle,
  toolbar
}) => (
  <Container>
    <PageHeader title={i18n.t("Products")}>
      <Button onClick={onAdd} color="primary" variant="contained">
        {i18n.t("Add product")} <AddIcon />
      </Button>
    </PageHeader>
    <Card>
      <ProductListFilter
        currentTab={currentTab}
        filtersList={filtersList}
        onAvailable={onAvailable}
        onAllProducts={onAllProducts}
        onOfStock={onOfStock}
        onCustomFilter={onCustomFilter}
      />
      <ProductList
        products={products}
        disabled={disabled}
        pageInfo={pageInfo}
        toolbar={toolbar}
        selected={selected}
        isChecked={isChecked}
        toggle={toggle}
        onNextPage={onNextPage}
        onPreviousPage={onPreviousPage}
        onRowClick={onRowClick}
      />
    </Card>
  </Container>
);
ProductListCard.displayName = "ProductListCard";
export default ProductListCard;
