import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../images/placeholder60x60.png";
import OrderDetailsPage, {
  OrderDetailsPageProps
} from "../../../orders/components/OrderDetailsPage";
import { countries, order as orderFixture } from "../../../orders/fixtures";
import { OrderStatus, PaymentStatusEnum } from "../../../types/globalTypes";
import Decorator from "../../Decorator";

const order = orderFixture(placeholderImage);

const props: OrderDetailsPageProps = {
  countries,
  errors: [],
  onBack: () => undefined,
  onBillingAddressEdit: undefined,
  onFulfillmentCancel: () => undefined,
  onFulfillmentTrackingNumberUpdate: () => undefined,
  onNoteAdd: undefined,
  onOrderCancel: undefined,
  onOrderFulfill: undefined,
  onPaymentCapture: undefined,
  onPaymentRefund: undefined,
  onPaymentRelease: undefined,
  onProductClick: undefined,
  onShippingAddressEdit: undefined,
  order
};

storiesOf("Views / Orders / Order details", module)
  .addDecorator(Decorator)
  .add("when loading data", () => (
    <OrderDetailsPage {...props} order={undefined} />
  ))
  .add("when loaded data", () => <OrderDetailsPage {...props} />)
  .add("as a draft", () => (
    <OrderDetailsPage
      {...props}
      order={{
        ...props.order,
        status: OrderStatus.DRAFT
      }}
    />
  ))
  .add("as a unpaid order", () => (
    <OrderDetailsPage
      {...props}
      order={{
        ...props.order,
        paymentStatus: PaymentStatusEnum.PREAUTH
      }}
    />
  ));
