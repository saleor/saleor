import Card from "@material-ui/core/Card";
import Hidden from "@material-ui/core/Hidden";
import IconButton from "@material-ui/core/IconButton";
import FilterListIcon from "@material-ui/icons/FilterList";
import * as React from "react";

import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import ProductList from "../../../components/ProductList";
import i18n from "../../../i18n";

interface ProductListCardProps {
  products?: Array<{
    id: string;
    name: string;
    productType: {
      name: string;
    };
    thumbnailUrl: string;
  }>;
  hasPreviousPage?: boolean;
  hasNextPage?: boolean;
  onFilter();
  onNextPage?();
  onPreviousPage?();
  onRowClick?(id: string);
}

export const ProductListCard: React.StatelessComponent<
  ProductListCardProps
> = ({
  products,
  hasNextPage,
  hasPreviousPage,
  onFilter,
  onNextPage,
  onPreviousPage,
  onRowClick
}) => (
  <Container width="md">
    <PageHeader title={i18n.t("Product list")}>
      <Hidden mdUp>
        <IconButton onClick={onFilter}>
          <FilterListIcon />
        </IconButton>
      </Hidden>
    </PageHeader>
    <Card>
      <ProductList
        products={products}
        hasNextPage={hasNextPage}
        hasPreviousPage={hasPreviousPage}
        onNextPage={onNextPage}
        onPreviousPage={onPreviousPage}
        onRowClick={onRowClick}
      />
    </Card>
  </Container>
);

export default ProductListCard;
