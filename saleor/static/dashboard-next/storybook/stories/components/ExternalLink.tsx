import { storiesOf } from "@storybook/react";
import React from "react";

import ExternalLink from "@saleor/components/ExternalLink";
import CardDecorator from "../../CardDecorator";
import Decorator from "../../Decorator";

storiesOf("Generics / External Link", module)
  .addDecorator(CardDecorator)
  .addDecorator(Decorator)
  .add("default", () => (
    <ExternalLink href="http://www.google.com">Link to google.com</ExternalLink>
  ))
  .add("new tab", () => (
    <ExternalLink href="http://www.google.com" target="_blank">
      Link to google.com
    </ExternalLink>
  ));
