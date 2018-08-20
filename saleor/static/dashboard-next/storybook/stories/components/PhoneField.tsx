import { storiesOf } from "@storybook/react";
import * as React from "react";

import PhoneField from "../../../components/PhoneField";
import { prefixes } from "../../../orders/fixtures";
import Decorator from "../../Decorator";

storiesOf("Generics / PhoneField", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <PhoneField
      prefixes={prefixes}
      name="phone"
      prefix="41"
      number="123 987 456"
      onChange={undefined}
    />
  ));
