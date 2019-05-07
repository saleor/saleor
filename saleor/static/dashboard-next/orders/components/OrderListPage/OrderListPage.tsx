import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import { Filter } from "../../../components/TableFilter";
import i18n from "../../../i18n";
import { ListActions, PageListProps } from "../../../types";
import { OrderList_orders_edges_node } from "../../types/OrderList";
import OrderList from "../OrderList";
import OrderListFilter, { OrderListFilterTabs } from "../OrderListFilter";

interface OrderListPageProps extends PageListProps, ListActions {
  orders: OrderList_orders_edges_node[];
  currentTab: OrderListFilterTabs;
  filtersList: Filter[];
  onAllProducts: () => void;
  onToFulfill: () => void;
  onToCapture: () => void;
  onCustomFilter: () => void;
}

const OrderListPage: React.StatelessComponent<OrderListPageProps> = ({
  disabled,
  onAdd,
  currentTab,
  filtersList,
  onAllProducts,
  onToFulfill,
  onToCapture,
  onCustomFilter,
  ...listProps
}) => (
  <Container>
    <PageHeader title={i18n.t("Orders")}>
      <Button
        color="primary"
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
      <OrderList disabled={disabled} {...listProps} />
    </Card>
  </Container>
);
OrderListPage.displayName = "OrderListPage";
export default OrderListPage;
