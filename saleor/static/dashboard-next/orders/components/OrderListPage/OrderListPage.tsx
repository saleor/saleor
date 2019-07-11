import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import AddIcon from "@material-ui/icons/Add";
import React from "react";

import Container from "@saleor/components/Container";
import PageHeader from "@saleor/components/PageHeader";
import i18n from "@saleor/i18n";
import { FilterPageProps, ListActions, PageListProps } from "@saleor/types";
import { OrderList_orders_edges_node } from "../../types/OrderList";
import { OrderListUrlFilters } from "../../urls";
import OrderList from "../OrderList";
import OrderListFilter from "../OrderListFilter";

export interface OrderListPageProps
  extends PageListProps,
    ListActions,
    FilterPageProps<OrderListUrlFilters> {
  orders: OrderList_orders_edges_node[];
}

const OrderListPage: React.FC<OrderListPageProps> = ({
  currencySymbol,
  currentTab,
  filtersList,
  filterTabs,
  initialSearch,
  onAdd,
  onAll,
  onSearchChange,
  onFilterAdd,
  onFilterSave,
  onTabChange,
  onFilterDelete,
  ...listProps
}) => (
  <Container>
    <PageHeader title={i18n.t("Orders")}>
      <Button color="primary" variant="contained" onClick={onAdd}>
        {i18n.t("Create order", { context: "button" })} <AddIcon />
      </Button>
    </PageHeader>
    <Card>
      <OrderListFilter
        allTabLabel={i18n.t("All Orders")}
        currencySymbol={currencySymbol}
        currentTab={currentTab}
        filterLabel={i18n.t("Select all orders where:")}
        filterTabs={filterTabs}
        filtersList={filtersList}
        initialSearch={initialSearch}
        searchPlaceholder={i18n.t("Search Orders...")}
        onAll={onAll}
        onSearchChange={onSearchChange}
        onFilterAdd={onFilterAdd}
        onFilterSave={onFilterSave}
        onTabChange={onTabChange}
        onFilterDelete={onFilterDelete}
      />
      <OrderList {...listProps} />
    </Card>
  </Container>
);
OrderListPage.displayName = "OrderListPage";
export default OrderListPage;
