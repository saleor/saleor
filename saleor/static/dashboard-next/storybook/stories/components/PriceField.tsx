import { storiesOf } from "@storybook/react";
import * as React from "react";

import PriceField, { PriceRangeField } from "../../../components/PriceField";

const value = {
  max: "30",
  min: "10"
};

storiesOf("Generics / PriceRangeField", module)
  .add("with no value", () => <PriceRangeField onChange={() => {}} />)
  .add("with value", () => (
    <PriceRangeField value={value} onChange={() => {}} />
  ))
  .add("with label", () => (
    <PriceRangeField label="Lorem ipsum" onChange={() => {}} />
  ))
  .add("with hint", () => (
    <PriceRangeField hint="Lorem ipsum" onChange={() => {}} />
  ))
  .add("with currency symbol", () => (
    <PriceRangeField currencySymbol="$" onChange={() => {}} />
  ))
  .add("disabled", () => <PriceRangeField disabled onChange={() => {}} />)
  .add("with label and hint", () => (
    <PriceRangeField label="Lorem" hint="Ipsum" onChange={() => {}} />
  ))
  .add("with value, label, currency symbol and hint", () => (
    <PriceRangeField
      value={value}
      label="Lorem"
      hint="Ipsum"
      onChange={() => {}}
      currencySymbol="$"
    />
  ))
  .add("with value, label, currency symbol and error", () => (
    <PriceRangeField
      value={value}
      label="Lorem"
      hint="Ipsum"
      error={true}
      onChange={() => {}}
      currencySymbol="$"
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
