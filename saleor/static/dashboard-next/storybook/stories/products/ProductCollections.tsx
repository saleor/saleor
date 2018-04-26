import { storiesOf } from "@storybook/react";
import * as React from "react";

import ProductCollections from "../../../products/components/ProductCollections";
import { collections } from "../../../products/fixtures";

storiesOf("Products / ProductCollections", module)
  .add("when loading data", () => <ProductCollections onRowClick={() => {}} />)
  .add("with no collections", () => (
    <ProductCollections collections={[]} onRowClick={() => {}} />
  ))
  .add("with collections", () => (
    <ProductCollections collections={collections} onRowClick={() => {}} />
  ));
