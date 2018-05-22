import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../images/placeholder60x60.png";
import { OrderStatus } from "../../../orders";
import OrderDetailsPage from "../../../orders/components/OrderDetailsPage";
import {
  countries,
  order as orderFixture,
  prefixes,
  variants
} from "../../../orders/fixtures";
import Decorator from "../../Decorator";

const order = orderFixture(placeholderImage);
const orderDraft = orderFixture(placeholderImage, {
  status: OrderStatus.DRAFT
});

storiesOf("Views / Orders / Order details", module)
  .addDecorator(Decorator)
  .add("when loading data", () => <OrderDetailsPage onBack={() => {}} />)
  .add("when loaded data", () => (
    <OrderDetailsPage
      countries={countries}
      order={order}
      prefixes={prefixes}
      user="admin@example.com"
      onBack={() => {}}
      onCreate={() => {}}
      onCustomerEmailClick={id => () => {}}
      onOrderCancel={() => {}}
      onPackingSlipClick={() => () => {}}
      onProductClick={() => {}}
    />
  ))
  .add("as a draft", () => (
    <OrderDetailsPage
      countries={countries}
      order={orderDraft}
      prefixes={prefixes}
      user="admin@example.com"
      variants={variants}
      variantsLoading={false}
      fetchVariants={() => {}}
      onBack={() => {}}
      onCreate={() => {}}
      onCustomerEmailClick={id => () => {}}
      onOrderCancel={() => {}}
      onPackingSlipClick={() => () => {}}
      onProductClick={() => {}}
    />
  ));
