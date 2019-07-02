import { storiesOf } from "@storybook/react";
import React from "react";

import Form from "@saleor/components/Form";
import MultiSelectField from "@saleor/components/MultiSelectField";
import CardDecorator from "../../CardDecorator";
import Decorator from "../../Decorator";

const choices = [
  { value: "1", label: "Apparel" },
  { value: "2", label: "Groceries" },
  { value: "3", label: "Books" },
  { value: "4", label: "Accessories" }
];

storiesOf("Generics / MultiSelectField", module)
  .addDecorator(CardDecorator)
  .addDecorator(Decorator)
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
  ))
  .add("interactive", () => (
    <Form initial={{ data: [choices[0].value] }}>
      {({ change, data }) => (
        <MultiSelectField
          choices={choices}
          onChange={change}
          value={data.data}
          label="Lorem"
          hint="Ipsum"
          name="data"
        />
      )}
    </Form>
  ));
