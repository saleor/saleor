import { storiesOf } from "@storybook/react";
import * as React from "react";

import CollectionProducts from "../../../collections/components/CollectionProducts";
import Decorator from "../../Decorator";

storiesOf("Collections / CollectionProducts", module)
  .addDecorator(Decorator)
  .add("default", () => <CollectionProducts />)
  .add("other", () => <CollectionProducts />);
