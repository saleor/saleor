import PrintIcon from "@material-ui/icons/Print";
import IconButton from "material-ui/IconButton";
import { withStyles } from "material-ui/styles";
import * as React from "react";

import { Container } from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import OrderCustomer from "../OrderCustomer";
import OrderFulfillment from "../OrderFulfillment/OrderFulfillment";
import OrderProducts from "../OrderProducts/OrderProducts";

interface AddressType {
  city: string;
  cityArea: string;
  companyName: string;
  country: string;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string;
  postalCode: string;
  streetAddress_1: string;
  streetAddress_2: string;
}
interface TaxedMoneyType {
  gross: {
    amount: number;
    currency: string;
  };
}
interface MoneyType {
  amount: number;
  currency: string;
}
interface OrderDetailsPageProps {
  order?: {
    id: string;
    client: {
      id: string;
      email: string;
      name: string;
    };
    shippingAddress?: AddressType;
    billingAddress?: AddressType;
    fulfillments: Array<{
      id: string;
      status: string;
      products: Array<{
        quantity: number;
        product: {
          id: string;
          name: string;
          thumbnailUrl: string;
        };
      }>;
    }>;
    products?: Array<{
      id: string;
      name: string;
      sku: string;
      thumbnailUrl: string;
      price: TaxedMoneyType;
      quantity: number;
    }>;
    subtotal: MoneyType;
    total: MoneyType;
  };
  onBack();
  onCustomerEmailClick?(id: string);
  onPrintClick?();
  onProductClick?(id: string);
}

const decorate = withStyles(theme => ({
  root: {
    display: "grid",
    gridTemplateColumns: "3fr 1fr",
    gridColumnGap: theme.spacing.unit * 2 + "px"
  }
}));
const OrderDetailsPage = decorate<OrderDetailsPageProps>(
  ({
    classes,
    order,
    onBack,
    onCustomerEmailClick,
    onPrintClick,
    onProductClick
  }) => (
    <Container width="md">
      <PageHeader
        title={
          order
            ? i18n.t("Order #{{ orderId }} summary", { orderId: order.id })
            : undefined
        }
        onBack={onBack}
      >
        <IconButton onClick={onPrintClick}>
          <PrintIcon />
        </IconButton>
      </PageHeader>
      <div className={classes.root}>
        <div>
          <OrderProducts
            products={order && order.products}
            subtotal={order && order.subtotal}
            total={order && order.total}
            onRowClick={onProductClick}
          />
          {order ? (
            order.fulfillments.map(fulfillment => (
              <OrderFulfillment
                products={fulfillment.products}
                status={fulfillment.status}
                id={fulfillment.id}
              />
            ))
          ) : (
            <OrderFulfillment />
          )}
        </div>
        <div>
          <OrderCustomer
            client={order ? order.client : undefined}
            shippingAddress={order ? order.shippingAddress : undefined}
            billingAddress={order ? order.billingAddress : undefined}
            onCustomerEmailClick={onCustomerEmailClick}
          />
        </div>
      </div>
    </Container>
  )
);
export default OrderDetailsPage;
