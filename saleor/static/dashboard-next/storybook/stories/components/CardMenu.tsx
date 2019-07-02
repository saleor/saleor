import { storiesOf } from "@storybook/react";
import React from "react";

import CardMenu, { CardMenuItem } from "@saleor/components/CardMenu";
import Decorator from "../../Decorator";

const menuItems: CardMenuItem[] = [
  { label: "Do this", onSelect: () => undefined },
  { label: "Or do this", onSelect: () => undefined },
  { label: "Or maybe this?", onSelect: () => undefined }
];

storiesOf("Generics / Card menu", module)
  .addDecorator(Decorator)
  .add("default", () => <CardMenu menuItems={menuItems} />);
