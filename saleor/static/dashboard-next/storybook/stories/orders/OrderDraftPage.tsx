import { Omit } from "@material-ui/core";
import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../images/placeholder60x60.png";
import OrderDraftPage, {
  OrderDraftPageProps
} from "../../../orders/components/OrderDraftPage";
import { clients, countries, draftOrder } from "../../../orders/fixtures";
import Decorator from "../../Decorator";

const order = draftOrder(placeholderImage);

const props: Omit<OrderDraftPageProps, "classes"> = {
  countries,
  disabled: false,
  fetchUsers: () => undefined,
  onBack: () => undefined,
  onBillingAddressEdit: undefined,
  onCustomerEdit: () => undefined,
  onDraftFinalize: () => undefined,
  onDraftRemove: () => undefined,
  onNoteAdd: undefined,
  onOrderLineAdd: () => undefined,
  onOrderLineChange: () => undefined,
  onOrderLineRemove: () => () => undefined,
  onProductClick: undefined,
  onShippingAddressEdit: undefined,
  onShippingMethodEdit: undefined,
  order,
  saveButtonBarState: "default",
  users: clients,
  usersLoading: false
};

storiesOf("Views / Orders / Order draft", module)
  .addDecorator(Decorator)
  .add("default", () => <OrderDraftPage {...props} />)
  .add("loading", () => (
    <OrderDraftPage {...props} disabled={true} order={undefined} />
  ))
  .add("without lines", () => (
    <OrderDraftPage {...props} order={{ ...order, lines: [] }} />
  ));
