import { storiesOf } from "@storybook/react";
import * as React from "react";
import * as placeholderImage from "../../../../images/placeholder60x60.png";
import HomePage, { HomePageProps } from "../../../home/components/HomePage";
import { shop as shopFixture } from "../../../home/fixtures";
import Decorator from "../../Decorator";

const shop = shopFixture(placeholderImage);

const HomePageProps: HomePageProps = {
  activities: shop.activities,
  daily: shop.daily,
  onProductClick: () => undefined,
  topProducts: shop.topProducts,
  userName: shop.userName
};

storiesOf("Views / HomePage", module)
  .addDecorator(Decorator)
  .add("default", () => <HomePage {...HomePageProps} />)
  .add("loading", () => (
    <HomePage
      {...HomePageProps}
      topProducts={undefined}
      daily={undefined}
      activities={undefined}
      userName={undefined}
    />
  ))
  .add("no data", () => (
    <HomePage {...HomePageProps} topProducts={[]} activities={[]} />
  ));
