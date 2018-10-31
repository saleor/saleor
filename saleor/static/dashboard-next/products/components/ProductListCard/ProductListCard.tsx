import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import { PageListProps } from "../../..";
import { CategoryDetails_category_products_edges_node } from "../../../categories/types/CategoryDetails";
import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import ProductList from "../../../components/ProductList";
import i18n from "../../../i18n";

interface ProductListCardProps extends PageListProps {
  products: CategoryDetails_category_products_edges_node[];
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
  onRowClick
}) => (
  <Container width="md">
    <PageHeader title={i18n.t("Products")}>
      <Button onClick={onAdd} color="secondary" variant="contained">
        {i18n.t("Add product")} <AddIcon />
      </Button>
    </PageHeader>
    <Card>
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

export default ProductListCard;
