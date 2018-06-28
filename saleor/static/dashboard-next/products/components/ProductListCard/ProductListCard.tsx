import Card from "@material-ui/core/Card";
import IconButton from "@material-ui/core/IconButton";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import { PageListProps } from "../../..";
import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import ProductList from "../../../components/ProductList";
import i18n from "../../../i18n";

interface ProductListCardProps extends PageListProps {
  products?: Array<{
    id: string;
    name: string;
    productType: {
      name: string;
    };
    thumbnailUrl: string;
  }>;
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
    <PageHeader title={i18n.t("Product list")}>
      <IconButton onClick={onAdd}>
        <AddIcon />
      </IconButton>
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
