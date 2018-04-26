import { storiesOf } from "@storybook/react";
import * as React from "react";

import ProductAvailabilityForm from "../../../products/components/ProductAvailabilityForm";

storiesOf("Products / ProductAvailabilityForm", module)
  .add("when loading data", () => (
    <ProductAvailabilityForm onChange={() => {}} />
  ))
  .add("with loaded data", () => (
    <ProductAvailabilityForm
      onChange={() => {}}
      available={true}
      availableOn={"04-10-2010"}
    />
  ));
