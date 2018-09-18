import { storiesOf } from "@storybook/react";
import * as React from "react";

import ExternalLink from "../../../components/ExternalLink";
import Decorator from "../../Decorator";

storiesOf("Generics / External Link", module)
  .addDecorator(Decorator)
  .add("default", () => <ExternalLink href="http://www.google.com">Link to google.com</ExternalLink>)
  .add("new tab", () => <ExternalLink href="http://www.google.com" target="_blank">Link to google.com</ExternalLink>);
