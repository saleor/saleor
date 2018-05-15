import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../images/placeholder60x60.png";
import OrderDetailsPage from "../../../orders/components/OrderDetailsPage";
import {
  countries,
  order as orderFixture,
  prefixes
} from "../../../orders/fixtures";
import Decorator from "../../Decorator";

const order = orderFixture(placeholderImage);

storiesOf("Views / Orders / Order details", module)
  .addDecorator(Decorator)
  .add("when loading data", () => <OrderDetailsPage onBack={() => {}} />)
  .add("when loaded data", () => (
    <OrderDetailsPage
      order={order}
      onBack={() => {}}
      user="admin@example.com"
      onCustomerEmailClick={id => () => {}}
      onProductClick={() => {}}
      onPackingSlipClick={() => () => {}}
      onOrderCancel={() => {}}
      prefixes={prefixes}
      countries={countries}
    />
  ));
