import { storiesOf } from "@storybook/react";
import * as React from "react";
import * as placeholderImage from "../../../../images/placeholder60x60.png";
import Dashbaord, { DashboardProps } from "../../../home/components/Dashbaord";
import { shop as shopFixture } from "../../../home/fixtures";
import Decorator from "../../Decorator";

const shop = shopFixture(placeholderImage);

const dashboardProps: DashboardProps = {
  ownerName: shop.ownerName
};

storiesOf("Views / Home / Dashboard", module)
  .addDecorator(Decorator)
  .add("default", () => <Dashbaord {...dashboardProps} />)
  .add("loading", () => <Dashbaord {...dashboardProps} />)
  .add("no data", () => <Dashbaord {...dashboardProps} />);
