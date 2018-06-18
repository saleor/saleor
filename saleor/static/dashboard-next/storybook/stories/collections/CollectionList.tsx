import { storiesOf } from "@storybook/react";
import * as React from "react";

import CollectionList from "../../../collections/components/CollectionList";
import Decorator from "../../Decorator";

storiesOf("Collections / CollectionList", module)
  .addDecorator(Decorator)
  .add("default", () => <CollectionList />)
  .add("other", () => <CollectionList />);
