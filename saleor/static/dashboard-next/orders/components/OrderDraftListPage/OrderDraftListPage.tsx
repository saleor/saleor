import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import { PageListProps } from "../../../types";
import { OrderDraftList_draftOrders_edges_node } from "../../types/OrderDraftList";
import OrderDraftList from "../OrderDraftList";

export interface OrderDraftListPageProps extends PageListProps {
  orders: OrderDraftList_draftOrders_edges_node[];
}

const OrderDraftListPage: React.StatelessComponent<OrderDraftListPageProps> = ({
  disabled,
  orders,
  pageInfo,
  onAdd,
  onNextPage,
  onPreviousPage,
  onRowClick
}) => (
  <Container>
    <PageHeader title={i18n.t("Draft Orders")}>
      <Button
        color="secondary"
        variant="contained"
        disabled={disabled}
        onClick={onAdd}
      >
        {i18n.t("Create order", { context: "button" })} <AddIcon />
      </Button>
    </PageHeader>
    <Card>
      <OrderDraftList
        disabled={disabled}
        onRowClick={onRowClick}
        orders={orders}
        pageInfo={pageInfo}
        onNextPage={onNextPage}
        onPreviousPage={onPreviousPage}
      />
    </Card>
  </Container>
);
OrderDraftListPage.displayName = "OrderDraftListPage";
export default OrderDraftListPage;
