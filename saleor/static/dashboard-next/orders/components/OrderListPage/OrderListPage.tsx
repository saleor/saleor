import { withStyles } from "material-ui/styles";
import * as React from "react";
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
          localized;
        };
      };
    }>;
  };
  onBack();
}

const decorate = withStyles(theme => ({ root: {} }));
const OrderListPage = decorate<OrderListPageProps>(
  ({ classes, orders, onBack }) => (
    // TODO: Wrap in container
    <>
      <PageHeader title={i18n.t("Orders")} onBack={onBack} />
      <OrderList
        orders={orders ? orders.edges.map(edge => edge.node) : undefined}
      />
    </>
  )
);
export default OrderListPage;
