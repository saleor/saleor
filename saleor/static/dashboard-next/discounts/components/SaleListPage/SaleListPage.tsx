import Button from "@material-ui/core/Button";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import { ListActions, PageListProps } from "../../../types";
import { SaleList_sales_edges_node } from "../../types/SaleList";
import SaleList from "../SaleList";

export interface SaleListPageProps extends PageListProps, ListActions {
  defaultCurrency: string;
  sales: SaleList_sales_edges_node[];
}

const SaleListPage: React.StatelessComponent<SaleListPageProps> = ({
  onAdd,
  ...listProps
}) => (
  <Container>
    <PageHeader title={i18n.t("Sales")}>
      <Button onClick={onAdd} variant="contained" color="primary">
        {i18n.t("Add sale")}
        <AddIcon />
      </Button>
    </PageHeader>
    <SaleList {...listProps} />
  </Container>
);
SaleListPage.displayName = "SaleListPage";
export default SaleListPage;
