import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import { CategoryDetails_category_products_edges_node } from "../../../categories/types/CategoryDetails";
import Container from "../../../components/Container";
import { FilterContentSubmitData } from "../../../components/Filter";
import PageHeader from "../../../components/PageHeader";
import ProductList from "../../../components/ProductList";
import { Filter } from "../../../components/TableFilter";
import i18n from "../../../i18n";
import { ListActions, PageListProps } from "../../../types";
import ProductListFilter from "../ProductListFilter";

export interface ProductListCardProps extends PageListProps, ListActions {
  currencySymbol: string;
  currentTab: number;
  filtersList: Filter[];
  products: CategoryDetails_category_products_edges_node[];
  onAllProducts: () => void;
  onSearchChange: (value: string) => void;
  onFilterAdd: (filter: FilterContentSubmitData) => void;
  onFilterSave: () => void;
  onTabChange: (tab: number) => void;
}

export const ProductListCard: React.StatelessComponent<
  ProductListCardProps
> = ({
  currencySymbol,
  currentTab,
  disabled,
  filtersList,
  pageInfo,
  products,
  onAdd,
  onAllProducts,
  onNextPage,
  onPreviousPage,
  onRowClick,
  isChecked,
  selected,
  toggle,
  toggleAll,
  toolbar,
  onSearchChange,
  onFilterAdd,
  onFilterSave,
  onTabChange
}) => (
  <Container>
    <PageHeader title={i18n.t("Products")}>
      <Button onClick={onAdd} color="primary" variant="contained">
        {i18n.t("Add product")} <AddIcon />
      </Button>
    </PageHeader>
    <Card>
      <ProductListFilter
        currencySymbol={currencySymbol}
        currentTab={currentTab}
        filtersList={filtersList}
        onAllProducts={onAllProducts}
        onSearchChange={onSearchChange}
        onFilterAdd={onFilterAdd}
        onFilterSave={onFilterSave}
        onTabChange={onTabChange}
      />
      <ProductList
        products={products}
        disabled={disabled}
        pageInfo={pageInfo}
        toolbar={toolbar}
        selected={selected}
        isChecked={isChecked}
        toggle={toggle}
        toggleAll={toggleAll}
        onNextPage={onNextPage}
        onPreviousPage={onPreviousPage}
        onRowClick={onRowClick}
      />
    </Card>
  </Container>
);
ProductListCard.displayName = "ProductListCard";
export default ProductListCard;
