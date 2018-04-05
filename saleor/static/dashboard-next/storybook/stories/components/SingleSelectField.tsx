import { storiesOf } from "@storybook/react";
import * as React from "react";

import SingleSelectField from "../../../components/SingleSelectField";

const choices = [
  { value: "1", label: "Apparel" },
  { value: "2", label: "Groceries" },
  { value: "3", label: "Books" },
  { value: "4", label: "Accessories" }
];

storiesOf("Generics / SingleSelectField", module)
  .add("with no value", () => (
    <SingleSelectField choices={choices} onChange={() => {}} />
  ))
  .add("with value", () => (
    <SingleSelectField
      choices={choices}
      onChange={() => {}}
      value={choices[0].value}
    />
  ))
  .add("with label", () => (
    <SingleSelectField
      choices={choices}
      onChange={() => {}}
      label="Lorem ipsum"
    />
  ))
  .add("with hint", () => (
    <SingleSelectField
      choices={choices}
      onChange={() => {}}
      hint="Lorem ipsum"
    />
  ))
  .add("with label and hint", () => (
    <SingleSelectField
      choices={choices}
      onChange={() => {}}
      label="Lorem"
      hint="Ipsum"
    />
  ))
  .add("with value, label and hint", () => (
    <SingleSelectField
      choices={choices}
      onChange={() => {}}
      value={choices[0].value}
      label="Lorem"
      hint="Ipsum"
    />
  ))
  .add("with error hint", () => (
    <SingleSelectField
      choices={choices}
      onChange={() => {}}
      hint="Lorem error"
      error={true}
    />
  ));
