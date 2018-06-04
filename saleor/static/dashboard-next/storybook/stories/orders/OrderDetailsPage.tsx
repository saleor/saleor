import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../images/placeholder60x60.png";
import { OrderStatus, PaymentStatus } from "../../../orders";
import OrderDetailsPage from "../../../orders/components/OrderDetailsPage";
import {
  clients,
  countries,
  order as orderFixture,
  prefixes,
  shippingMethods,
  variants
} from "../../../orders/fixtures";
import Decorator from "../../Decorator";

const order = orderFixture(placeholderImage);
const orderDraft = orderFixture(placeholderImage, {
  status: OrderStatus.DRAFT
});
const orderWithoutPayment = orderFixture(placeholderImage, {
  paymentStatus: PaymentStatus.PREAUTH
});

const callbacks = {
  onBack: () => {},
  onCreate: () => {},
  onCustomerEmailClick: id => () => {},
  onOrderCancel: () => {},
  onOrderLineChange: () => () => () => {},
  onOrderLineRemove: () => () => {},
  onPackingSlipClick: () => () => {},
  onPaymentRelease: () => {},
  onPrintClick: () => {},
  onProductClick: () => {}
};

storiesOf("Views / Orders / Order details", module)
  .addDecorator(Decorator)
  .add("when loading data", () => <OrderDetailsPage onBack={() => {}} />)
  .add("when loaded data", () => (
    <OrderDetailsPage
      countries={countries}
      order={order}
      prefixes={prefixes}
      user="admin@example.com"
      {...callbacks}
    />
  ))
  .add("as a draft", () => (
    <OrderDetailsPage
      countries={countries}
      order={orderDraft}
      prefixes={prefixes}
      shippingMethods={shippingMethods}
      user="admin@example.com"
      users={clients}
      variants={variants}
      variantsLoading={false}
      fetchShippingMethods={() => {}}
      fetchUsers={() => {}}
      fetchVariants={() => {}}
      {...callbacks}
    />
  ))
  .add("as a unpaid order", () => (
    <OrderDetailsPage
      countries={countries}
      order={orderWithoutPayment}
      prefixes={prefixes}
      shippingMethods={shippingMethods}
      user="admin@example.com"
      users={clients}
      variants={variants}
      variantsLoading={false}
      fetchShippingMethods={() => {}}
      fetchUsers={() => {}}
      fetchVariants={() => {}}
      {...callbacks}
    />
  ));
