import { storiesOf } from "@storybook/react";
import * as React from "react";

import CollectionListPage from "../../../collections/components/CollectionListPage";
import Decorator from "../../Decorator";

storiesOf("Collections / CollectionListPage", module)
  .addDecorator(Decorator)
  .add("default", () => <CollectionListPage />)
  .add("other", () => <CollectionListPage />);
