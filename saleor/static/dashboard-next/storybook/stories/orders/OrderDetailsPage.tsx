import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../images/placeholder60x60.png";
import { PaymentStatus } from "../../../orders";
import OrderDetailsPage from "../../../orders/components/OrderDetailsPage";
import {
  clients,
  countries,
  order as orderFixture,
  shippingMethods,
  variants
} from "../../../orders/fixtures";
import { OrderStatus } from "../../../types/globalTypes";
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
  onOrderCancel: undefined,
  onOrderFulfill: undefined,
  onOrderLineChange: () => () => () => undefined,
  onOrderLineRemove: () => () => undefined,
  onPackingSlipClick: () => undefined,
  onPaymentCapture: undefined,
  onPaymentRefund: undefined,
  onPaymentRelease: undefined,
  onPrintClick: undefined,
  onProductAdd: undefined,
  onProductClick: undefined
};

storiesOf("Views / Orders / Order details", module)
  .addDecorator(Decorator)
  .add("when loading data", () => <OrderDetailsPage {...callbacks} />)
  .add("when loaded data", () => (
    <OrderDetailsPage
      countries={countries}
      order={order}
      user={{ email: "admin@example.com" }}
      {...callbacks}
    />
  ))
  .add("as a draft", () => (
    <OrderDetailsPage
      countries={countries}
      order={orderDraft}
      shippingMethods={shippingMethods}
      user={{ email: "admin@example.com" }}
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
      shippingMethods={shippingMethods}
      user={{ email: "admin@example.com" }}
      users={clients}
      variants={variants}
      variantsLoading={false}
      fetchShippingMethods={undefined}
      fetchUsers={undefined}
      fetchVariants={undefined}
      {...callbacks}
    />
  ));
