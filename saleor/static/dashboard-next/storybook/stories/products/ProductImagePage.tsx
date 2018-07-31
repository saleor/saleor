import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholder from "../../../../images/placeholder1080x1080.png";
import ProductImagePage from "../../../products/components/ProductImagePage";
import Decorator from "../../Decorator";

storiesOf("Views / Products / Product image details", module)
  .addDecorator(Decorator)
  .add("when loaded data", () => (
    <ProductImagePage
      onSubmit={() => {}}
      onBack={() => {}}
      image={placeholder}
    />
  ))
  .add("when loading data", () => (
    <ProductImagePage disabled={true} onSubmit={() => {}} onBack={() => {}} />
  ));
