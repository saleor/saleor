import { storiesOf } from "@storybook/react";
import * as React from "react";
import * as placeholderImage from "../../../../images/placeholder60x60.png";
import Dashbaord, { DashboardProps } from "../../../home/components/Dashbaord";
import { shop as shopFixture } from "../../../home/fixtures";
import Decorator from "../../Decorator";

const shop = shopFixture(placeholderImage);

const dashboardProps: DashboardProps = {
  daily: shop.daily,
  notifications: shop.notifications,
  onRowClick: () => undefined,
  ownerName: shop.ownerName,
  toOrders: () => undefined,
  toPayments: () => undefined,
  toProblems: () => undefined,
  toProductsOut: () => undefined,
  topProducts: shop.topProducts
};

storiesOf("Views / Home / Dashboard", module)
  .addDecorator(Decorator)
  .add("default", () => <Dashbaord {...dashboardProps} />)
  .add("loading", () => (
    <Dashbaord
      {...dashboardProps}
      topProducts={undefined}
      daily={undefined}
      notifications={undefined}
    />
  ))
  .add("no data", () => (
    <Dashbaord
      {...dashboardProps}
      topProducts={[]}
      notifications={{
        orders: 0,
        payments: 0,
        problems: 0,
        productsOut: 0
      }}
    />
  ));
