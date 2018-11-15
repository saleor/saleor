import Button from "@material-ui/core/Button";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import { PageListProps } from "../../../types";
import { OrderList_orders_edges_node } from "../../types/OrderList";
import OrderList from "../OrderList";

interface OrderListPageProps extends PageListProps {
  orders: OrderList_orders_edges_node[];
}

const OrderListPage: React.StatelessComponent<OrderListPageProps> = ({
  disabled,
  orders,
  pageInfo,
  onAdd,
  onNextPage,
  onPreviousPage,
  onRowClick
}) => (
  <Container width="md">
    <PageHeader title={i18n.t("Orders")}>
      <Button
        color="secondary"
        variant="contained"
        disabled={disabled}
        onClick={onAdd}
      >
        {i18n.t("Create order", { context: "button" })} <AddIcon />
      </Button>
    </PageHeader>
    <OrderList
      disabled={disabled}
      onRowClick={onRowClick}
      orders={orders}
      pageInfo={pageInfo}
      onNextPage={onNextPage}
      onPreviousPage={onPreviousPage}
    />
  </Container>
);
OrderListPage.displayName = "OrderListPage";
export default OrderListPage;
