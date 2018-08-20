import { storiesOf } from "@storybook/react";
import * as React from "react";

import MultiSelectField from "../../../components/MultiSelectField";

const choices = [
  { value: "1", label: "Apparel" },
  { value: "2", label: "Groceries" },
  { value: "3", label: "Books" },
  { value: "4", label: "Accessories" }
];

storiesOf("Generics / MultiSelectField", module)
  .add("with no value", () => (
    <MultiSelectField choices={choices} onChange={undefined} />
  ))
  .add("with value", () => (
    <MultiSelectField
      choices={choices}
      onChange={undefined}
      value={[choices[0].value]}
    />
  ))
  .add("with label", () => (
    <MultiSelectField
      choices={choices}
      onChange={undefined}
      label="Lorem ipsum"
    />
  ))
  .add("with hint", () => (
    <MultiSelectField
      choices={choices}
      onChange={undefined}
      hint="Lorem ipsum"
    />
  ))
  .add("with label and hint", () => (
    <MultiSelectField
      choices={choices}
      onChange={undefined}
      label="Lorem"
      hint="Ipsum"
    />
  ))
  .add("with value, label and hint", () => (
    <MultiSelectField
      choices={choices}
      onChange={undefined}
      value={[choices[0].value]}
      label="Lorem"
      hint="Ipsum"
    />
  ))
  .add("with error hint", () => (
    <MultiSelectField
      choices={choices}
      onChange={undefined}
      hint="Lorem error"
      error={true}
    />
  ));
