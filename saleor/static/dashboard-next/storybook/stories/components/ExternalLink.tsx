import { storiesOf } from "@storybook/react";
import * as React from "react";

import ExternalLink from "../../../components/ExternalLink";
import Decorator from "../../Decorator";

storiesOf("Generics / ExternalLink", module)
  .addDecorator(Decorator)
  .add("default", () => <ExternalLink href="http://www.google.pl" />);
