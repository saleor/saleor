import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholder from "../../../../images/placeholder255x255.png";
import ProductImagePage from "../../../products/components/ProductImagePage";

storiesOf("Products / ProductImagePage", module)
  .add("loading", () => (
    <ProductImagePage loading={true} onSubmit={() => {}} onBack={() => {}} />
  ))
  .add("data loaded", () => (
    <ProductImagePage
      onSubmit={() => {}}
      onBack={() => {}}
      image={placeholder}
    />
  ));
