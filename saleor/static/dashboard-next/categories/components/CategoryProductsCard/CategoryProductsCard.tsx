import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import IconButton from "@material-ui/core/IconButton";
import DeleteIcon from "@material-ui/icons/Delete";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import ProductList from "../../../components/ProductList";
import useBulkActions from "../../../hooks/useBulkActions";
import i18n from "../../../i18n";
import { ListActionProps, PageListProps } from "../../../types";
import { CategoryDetails_category_products_edges_node } from "../../types/CategoryDetails";

interface CategoryProductsCardProps
  extends PageListProps,
    ListActionProps<"onBulkDelete"> {
  products: CategoryDetails_category_products_edges_node[];
  categoryName: string;
}

export const CategoryProductsCard: React.StatelessComponent<
  CategoryProductsCardProps
> = ({
  products,
  disabled,
  pageInfo,
  onAdd,
  onBulkDelete,
  onNextPage,
  onPreviousPage,
  onRowClick,
  categoryName
}) => {
  const { isMember: isChecked, listElements, toggle } = useBulkActions(
    products
  );

  return (
    <Card>
      <CardTitle
        title={i18n.t("Products in {{ categoryName }}", { categoryName })}
        toolbar={
          <Button color="primary" variant="text" onClick={onAdd}>
            {i18n.t("Add product")}
          </Button>
        }
      />
      <ProductList
        products={products}
        disabled={disabled}
        pageInfo={pageInfo}
        onNextPage={onNextPage}
        onPreviousPage={onPreviousPage}
        onRowClick={onRowClick}
        selected={listElements.length}
        isChecked={isChecked}
        toggle={toggle}
        toolbar={
          <>
            <IconButton
              color="primary"
              onClick={() => onBulkDelete(listElements)}
            >
              <DeleteIcon />
            </IconButton>
          </>
        }
      />
    </Card>
  );
};

CategoryProductsCard.displayName = "CategoryProductsCard";
export default CategoryProductsCard;
