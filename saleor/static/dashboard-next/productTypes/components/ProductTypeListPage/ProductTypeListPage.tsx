import Button from "@material-ui/core/Button";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import { PageListProps } from "../../..";
import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import {
  ProductTypeList_productTypes_edges_node_productAttributes,
  ProductTypeList_productTypes_edges_node_variantAttributes
} from "../../types/ProductTypeList";
import ProductTypeList from "../ProductTypeList";

interface ProductTypeListPageProps extends PageListProps {
  productTypes?: Array<{
    id: string;
    name?: string;
    hasVariants?: boolean;
    productAttributes?: ProductTypeList_productTypes_edges_node_productAttributes[];
    variantAttributes?: ProductTypeList_productTypes_edges_node_variantAttributes[];
  }>;
}

const ProductTypeListPage: React.StatelessComponent<
  ProductTypeListPageProps
> = ({
  productTypes,
  disabled,
  pageInfo,
  onAdd,
  onNextPage,
  onPreviousPage,
  onRowClick
}) => (
  <Container width="md">
    <PageHeader title={i18n.t("Product types")}>
      <Button
        color="secondary"
        variant="contained"
        disabled={disabled}
        onClick={onAdd}
      >
        {i18n.t("Add product type")} <AddIcon />
      </Button>
    </PageHeader>
    <ProductTypeList
      productTypes={productTypes}
      disabled={disabled}
      pageInfo={pageInfo}
      onNextPage={onNextPage}
      onPreviousPage={onPreviousPage}
      onRowClick={onRowClick}
    />
  </Container>
);
ProductTypeListPage.displayName = "ProductTypeListPage";
export default ProductTypeListPage;
