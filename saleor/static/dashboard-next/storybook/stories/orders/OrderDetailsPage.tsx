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
  onBack: () => undefined,
  onCreate: undefined,
  onCustomerEmailClick: () => undefined,
  onOrderCancel: undefined,
  onOrderLineChange: () => () => () => undefined,
  onOrderLineRemove: () => () => undefined,
  onPackingSlipClick: () => undefined,
  onPaymentRelease: undefined,
  onPrintClick: undefined,
  onProductClick: undefined
};

storiesOf("Views / Orders / Order details", module)
  .addDecorator(Decorator)
  .add("when loading data", () => <OrderDetailsPage onBack={() => undefined} />)
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
      fetchShippingMethods={undefined}
      fetchUsers={undefined}
      fetchVariants={undefined}
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
      fetchShippingMethods={undefined}
      fetchUsers={undefined}
      fetchVariants={undefined}
      {...callbacks}
    />
  ));
