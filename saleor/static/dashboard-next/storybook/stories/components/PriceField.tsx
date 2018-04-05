import { storiesOf } from "@storybook/react";
import * as React from "react";

import PriceField from "../../../components/PriceField";

const value = {
  max: "30",
  min: "10"
};

storiesOf("Generics / PriceField", module)
  .add("with no value", () => <PriceField onChange={() => {}} />)
  .add("with value", () => <PriceField value={value} onChange={() => {}} />)
  .add("with label", () => (
    <PriceField label="Lorem ipsum" onChange={() => {}} />
  ))
  .add("with hint", () => <PriceField hint="Lorem ipsum" onChange={() => {}} />)
  .add("with label and hint", () => (
    <PriceField label="Lorem" hint="Ipsum" onChange={() => {}} />
  ))
  .add("with value, label and hint", () => (
    <PriceField value={value} label="Lorem" hint="Ipsum" onChange={() => {}} />
  ))
  .add("with value, label and error", () => (
    <PriceField
      value={value}
      label="Lorem"
      hint="Ipsum"
      error={true}
      onChange={() => {}}
    />
  ));
