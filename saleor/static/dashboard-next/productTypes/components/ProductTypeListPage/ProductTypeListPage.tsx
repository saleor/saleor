import Button from "@material-ui/core/Button";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import AppHeader from "../../../components/AppHeader";
import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import { ListActions, PageListProps } from "../../../types";
import { ProductTypeList_productTypes_edges_node } from "../../types/ProductTypeList";
import ProductTypeList from "../ProductTypeList";

interface ProductTypeListPageProps extends PageListProps, ListActions {
  productTypes: ProductTypeList_productTypes_edges_node[];
  onBack: () => void;
}

const ProductTypeListPage: React.StatelessComponent<
  ProductTypeListPageProps
> = ({ disabled, onAdd, onBack, ...listProps }) => (
  <Container>
    <AppHeader onBack={onBack}>{i18n.t("Configuration")}</AppHeader>
    <PageHeader title={i18n.t("Product types")}>
      <Button
        color="primary"
        variant="contained"
        disabled={disabled}
        onClick={onAdd}
      >
        {i18n.t("Add product type")} <AddIcon />
      </Button>
    </PageHeader>
    <ProductTypeList disabled={disabled} {...listProps} />
  </Container>
);
ProductTypeListPage.displayName = "ProductTypeListPage";
export default ProductTypeListPage;
