import Button from "@material-ui/core/Button";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import { transformOrderStatus, transformPaymentStatus } from "../../";
import { PageListProps } from "../../..";
import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import OrderList from "../OrderList";

interface OrderListPageProps extends PageListProps {
  orders?: Array<{
    id: string;
    number: number;
    status: string;
    client: {
      id: string;
      email: string;
    };
    created: string;
    paymentStatus: string;
    price: {
      amount: number;
      currency: string;
    };
  }>;
}

const OrderListPage: React.StatelessComponent<OrderListPageProps> = ({
  disabled,
  orders,
  pageInfo,
  onAdd,
  onNextPage,
  onPreviousPage,
  onRowClick
}) => {
  const orderList = orders
    ? orders.map(order => ({
        ...order,
        orderStatus: transformOrderStatus(order.status),
        paymentStatus: transformPaymentStatus(order.paymentStatus)
      }))
    : undefined;
  return (
    <Container width="md">
      <PageHeader title={i18n.t("Orders")}>
        <Button
          color="secondary"
          variant="contained"
          disabled={disabled}
          onClick={onAdd}
        >
          {i18n.t("Add order")} <AddIcon />
        </Button>
      </PageHeader>
      <OrderList
        disabled={disabled}
        onRowClick={onRowClick}
        orders={orderList}
        pageInfo={pageInfo}
        onNextPage={onNextPage}
        onPreviousPage={onPreviousPage}
      />
    </Container>
  );
};
export default OrderListPage;
