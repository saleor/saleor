import { storiesOf } from "@storybook/react";
import * as React from "react";

import ProductTypeListPage from "../../../productTypes/components/ProductTypeListPage";
import Decorator from "../../Decorator";

storiesOf("ProductTypes / ProductTypeListPage", module)
  .addDecorator(Decorator)
  .add("default", () => <ProductTypeListPage />)
  .add("other", () => <ProductTypeListPage />);
