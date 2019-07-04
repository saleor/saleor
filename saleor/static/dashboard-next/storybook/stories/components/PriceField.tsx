import { storiesOf } from "@storybook/react";
import React from "react";

import PriceField from "@saleor/components/PriceField";
import CardDecorator from "../../CardDecorator";
import Decorator from "../../Decorator";

storiesOf("Generics / Price input", module)
  .addDecorator(CardDecorator)
  .addDecorator(Decorator)
  .add("with no value", () => <PriceField onChange={undefined} />)
  .add("with value", () => <PriceField value={"30"} onChange={undefined} />)
  .add("with label", () => (
    <PriceField label="Lorem ipsum" onChange={undefined} />
  ))
  .add("with hint", () => (
    <PriceField hint="Lorem ipsum" onChange={undefined} />
  ))
  .add("with currency symbol", () => (
    <PriceField currencySymbol="$" onChange={undefined} />
  ))
  .add("disabled", () => <PriceField disabled onChange={undefined} />)
  .add("with label and hint", () => (
    <PriceField label="Lorem" hint="Ipsum" onChange={undefined} />
  ))
  .add("with value, label, currency symbol and hint", () => (
    <PriceField
      value={"30"}
      label="Lorem"
      hint="Ipsum"
      onChange={undefined}
      currencySymbol="$"
    />
  ))
  .add("with value, label, currency symbol and error", () => (
    <PriceField
      value={"30"}
      label="Lorem"
      hint="Ipsum"
      error={true}
      onChange={undefined}
      currencySymbol="$"
    />
  ));
