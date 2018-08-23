import Button from "@material-ui/core/Button";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import { PageListProps } from "../../..";
import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import ProductTypeList from "../ProductTypeList";

interface AttributeType {
  id: string;
  sortNumber?: number;
  name?: string;
}
interface AttributeEdgeType {
  node: AttributeType;
}
interface ProductTypeListPageProps extends PageListProps {
  productTypes?: Array<{
    id: string;
    name?: string;
    hasVariants?: boolean;
    productAttributes?: {
      edges: AttributeEdgeType[];
    };
    variantAttributes?: {
      edges: AttributeEdgeType[];
    };
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
