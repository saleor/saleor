import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../images/placeholder255x255.png";
import { pageListProps } from "../../../fixtures";
import ProductListCard from "../../../products/components/ProductListCard";
import { products as productFixture } from "../../../products/fixtures";
import Decorator from "../../Decorator";

const products = productFixture(placeholderImage);

// disabled: false,
// onAdd: undefined,
// onNextPage: undefined,
// onPreviousPage: undefined,
// onRowClick: () => undefined,
// pageInfo

storiesOf("Views / Products / Product list", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <ProductListCard products={products} {...pageListProps.default} />
  ))
  .add("loading", () => <ProductListCard {...pageListProps.loading} />)
  .add("no data", () => (
    <ProductListCard products={[]} {...pageListProps.default} />
  ));
