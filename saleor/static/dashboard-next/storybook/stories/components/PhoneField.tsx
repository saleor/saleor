import { storiesOf } from "@storybook/react";
import * as React from "react";

import PhoneField from "../../../components/PhoneField";
import { prefixes } from "../../../orders/fixtures";
import Decorator from "../../Decorator";

storiesOf("Components / PhoneField", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <PhoneField
      prefixes={prefixes}
      name="phone"
      value={{ prefix: "41", number: "123 012 239" }}
      onChange={() => {}}
    />
  ));
