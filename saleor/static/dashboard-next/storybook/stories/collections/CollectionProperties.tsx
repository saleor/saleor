import { storiesOf } from "@storybook/react";
import * as React from "react";

import CollectionProperties from "../../../collections/components/CollectionProperties";
import Decorator from "../../Decorator";

storiesOf("Collections / CollectionProperties", module)
  .addDecorator(Decorator)
  .add("default", () => <CollectionProperties />)
  .add("other", () => <CollectionProperties />);
