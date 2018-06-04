import { withStyles } from "material-ui/styles";
import * as React from "react";

import { transformOrderStatus, transformPaymentStatus } from "../../";
import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import OrderList from "../OrderList";

interface OrderListPageProps {
  orders?: {
    edges: Array<{
      node: {
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
      };
    }>;
  };
  dateNow?: number;
  onBack();
  onRowClick(id: string);
}

const decorate = withStyles(theme => ({ root: {} }));
const OrderListPage = decorate<OrderListPageProps>(
  ({ classes, dateNow, orders, onBack, onRowClick }) => {
    const orderList = orders
      ? orders.edges.map(edge => ({
          ...edge.node,
          orderStatus: transformOrderStatus(edge.node.status),
          paymentStatus: transformPaymentStatus(edge.node.paymentStatus)
        }))
      : undefined;
    return (
      <Container width="md">
        <PageHeader title={i18n.t("Orders")} onBack={onBack} />
        <OrderList
          dateNow={dateNow}
          onRowClick={onRowClick}
          orders={orderList}
        />
      </Container>
    );
  }
);
export default OrderListPage;
