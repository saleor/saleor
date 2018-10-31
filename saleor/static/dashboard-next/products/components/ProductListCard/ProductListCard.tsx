import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import { CategoryDetails_category_products_edges_node } from "../../../categories/types/CategoryDetails";
import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import ProductList from "../../../components/ProductList";
import i18n from "../../../i18n";
import { PageListProps } from "../../../types";
import ProductListFilter from "../ProductListFilter";

export interface Filter {
  label: string;
  onClick: () => void;
}
interface ProductListCardProps extends PageListProps {
  currentTab: number;
  filtersList: Filter[];
  products: CategoryDetails_category_products_edges_node[];
  onAllProducts: () => void;
  onAvailable: () => void;
  onOfStock: () => void;
}

export const ProductListCard: React.StatelessComponent<
  ProductListCardProps
> = ({
  products,
  disabled,
  pageInfo,
  onAdd,
  onNextPage,
  onPreviousPage,
  onRowClick,
  filtersList,
  currentTab,
  onAllProducts,
  onAvailable,
  onOfStock
}) => (
  <Container width="md">
    <PageHeader title={i18n.t("Products")}>
      <Button onClick={onAdd} color="secondary" variant="contained">
        {i18n.t("Add product")} <AddIcon />
      </Button>
    </PageHeader>
    <Card>
      <ProductListFilter
        currentTab={currentTab}
        filtersList={filtersList}
        onAllProducts={onAllProducts}
        onAvailable={onAvailable}
        onOfStock={onOfStock}
      />
      <ProductList
        products={products}
        disabled={disabled}
        pageInfo={pageInfo}
        onNextPage={onNextPage}
        onPreviousPage={onPreviousPage}
        onRowClick={onRowClick}
      />
    </Card>
  </Container>
);
ProductListCard.displayName = "ProductListCard";
export default ProductListCard;
