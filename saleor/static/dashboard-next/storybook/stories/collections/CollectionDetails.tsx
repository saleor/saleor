import { storiesOf } from "@storybook/react";
import * as React from "react";

import CollectionDetails from "../../../collections/components/CollectionDetails";
import Decorator from "../../Decorator";

storiesOf("Collections / CollectionDetails", module)
  .addDecorator(Decorator)
  .add("default", () => <CollectionDetails />)
  .add("other", () => <CollectionDetails />);
