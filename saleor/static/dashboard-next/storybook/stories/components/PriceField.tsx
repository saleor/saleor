import { storiesOf } from "@storybook/react";
import * as React from "react";

import PriceField, { PriceRangeField } from "../../../components/PriceField";

const value = {
  max: "30",
  min: "10"
};

storiesOf("Generics / PriceRangeField", module)
  .add("with value", () => (
    <PriceRangeField
      currencySymbol="USD"
      name="priceField"
      onChange={() => {}}
      value={value}
    />
  ))
  .add("with label", () => (
    <PriceRangeField
      currencySymbol="USD"
      label="Lorem ipsum"
      name="priceField"
      onChange={() => {}}
      value={value}
    />
  ))
  .add("with hint", () => (
    <PriceRangeField
      currencySymbol="USD"
      hint="Lorem ipsum"
      name="priceField"
      onChange={() => {}}
      value={value}
    />
  ))
  .add("disabled", () => (
    <PriceRangeField
      currencySymbol="USD"
      disabled
      name="priceField"
      onChange={() => {}}
      value={value}
    />
  ))
  .add("with label and hint", () => (
    <PriceRangeField
      currencySymbol="USD"
      hint="Ipsum"
      label="Lorem"
      name="priceField"
      onChange={() => {}}
      value={value}
    />
  ))
  .add("with value, label, currency symbol and hint", () => (
    <PriceRangeField
      currencySymbol="USD"
      hint="Ipsum"
      label="Lorem"
      name="priceField"
      onChange={() => {}}
      value={value}
    />
  ))
  .add("with value, label, currency symbol and error", () => (
    <PriceRangeField
      currencySymbol="USD"
      error={true}
      hint="Ipsum"
      label="Lorem"
      name="priceField"
      onChange={() => {}}
      value={value}
    />
  ));

storiesOf("Generics / PriceField", module)
  .add("with no value", () => <PriceField onChange={() => {}} />)
  .add("with value", () => <PriceField value={"30"} onChange={() => {}} />)
  .add("with label", () => (
    <PriceField label="Lorem ipsum" onChange={() => {}} />
  ))
  .add("with hint", () => <PriceField hint="Lorem ipsum" onChange={() => {}} />)
  .add("with currency symbol", () => (
    <PriceField currencySymbol="$" onChange={() => {}} />
  ))
  .add("disabled", () => <PriceField disabled onChange={() => {}} />)
  .add("with label and hint", () => (
    <PriceField label="Lorem" hint="Ipsum" onChange={() => {}} />
  ))
  .add("with value, label, currency symbol and hint", () => (
    <PriceField
      value={"30"}
      label="Lorem"
      hint="Ipsum"
      onChange={() => {}}
      currencySymbol="$"
    />
  ))
  .add("with value, label, currency symbol and error", () => (
    <PriceField
      value={"30"}
      label="Lorem"
      hint="Ipsum"
      error={true}
      onChange={() => {}}
      currencySymbol="$"
    />
  ));
