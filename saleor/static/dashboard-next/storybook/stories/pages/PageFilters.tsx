import { storiesOf } from "@storybook/react";
import * as React from "react";

import PageFilters from "../../../page/components/PageFilters";

storiesOf("Pages / PageFilters", module)
  .add("with initial data", () => (
    <PageFilters
      handleClear={() => {}}
      handleSubmit={() => {}}
      formState={{ title: "Initial title", url: "initial-url" }}
    />
  ))
  .add("without initial data", () => (
    <PageFilters handleClear={() => {}} handleSubmit={() => {}} />
  ));
