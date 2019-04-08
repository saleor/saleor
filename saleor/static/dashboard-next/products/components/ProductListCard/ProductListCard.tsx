import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import IconButton from "@material-ui/core/IconButton";
import AddIcon from "@material-ui/icons/Add";
import DeleteIcon from "@material-ui/icons/Delete";
import * as CRC from "crc-32";
import * as React from "react";

import { CategoryDetails_category_products_edges_node } from "../../../categories/types/CategoryDetails";
import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import ProductList from "../../../components/ProductList";
import { Filter } from "../../../components/TableFilter";
import useBulkActions from "../../../hooks/useBulkActions";
import useListSelector from "../../../hooks/useListSelector";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { ListActionProps, PageListProps } from "../../../types";
import ProductListFilter, { ProductListFilterTabs } from "../ProductListFilter";

interface ProductListCardProps
  extends PageListProps,
    ListActionProps<"onBulkDelete" | "onBulkPublish" | "onBulkUnpublish"> {
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
  onBulkDelete,
  onBulkPublish,
  onBulkUnpublish,
  onCustomFilter,
  onNextPage,
  onOfStock,
  onPreviousPage,
  onRowClick
}) => {
  const { isMember: isChecked, listElements, toggle } = useBulkActions(
    products
  );

  return (
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
          toolbar={
            <>
              <Button
                color="primary"
                onClick={() => onBulkUnpublish(listElements)}
              >
                {i18n.t("Unpublish")}
              </Button>
              <Button
                color="primary"
                onClick={() => onBulkPublish(listElements)}
              >
                {i18n.t("Publish")}
              </Button>
              <IconButton
                color="primary"
                onClick={() => onBulkDelete(listElements)}
              >
                <DeleteIcon />
              </IconButton>
            </>
          }
          selected={listElements.length}
          isChecked={isChecked}
          toggle={toggle}
          onNextPage={onNextPage}
          onPreviousPage={onPreviousPage}
          onRowClick={onRowClick}
        />
      </Card>
    </Container>
  );
};
ProductListCard.displayName = "ProductListCard";
export default ProductListCard;
