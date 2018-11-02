import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import { Filter } from "../../../components/TableFilter";
import i18n from "../../../i18n";
import { PageListProps } from "../../../types";
import { OrderList_orders_edges_node } from "../../types/OrderList";
import OrderList from "../OrderList";
import OrderListFilter from "../OrderListFilter";

interface OrderListPageProps extends PageListProps {
  orders: OrderList_orders_edges_node[];
  currentTab: number;
  filtersList: Filter[];
  onAllProducts: () => void;
  onToFulfill: () => void;
  onToCapture: () => void;
  onCustomFilter: () => void;
}

const OrderListPage: React.StatelessComponent<OrderListPageProps> = ({
  disabled,
  orders,
  pageInfo,
  onAdd,
  onNextPage,
  onPreviousPage,
  onRowClick,
  currentTab,
  filtersList,
  onAllProducts,
  onToFulfill,
  onToCapture,
  onCustomFilter
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
    <Card>
      <OrderListFilter
        currentTab={currentTab}
        filtersList={filtersList}
        onAllProducts={onAllProducts}
        onToFulfill={onToFulfill}
        onToCapture={onToCapture}
        onCustomFilter={onCustomFilter}
      />
      <OrderList
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
OrderListPage.displayName = "OrderListPage";
export default OrderListPage;
