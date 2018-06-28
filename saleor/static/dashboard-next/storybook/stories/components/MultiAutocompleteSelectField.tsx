import { storiesOf } from "@storybook/react";
import * as React from "react";

import Form from "../../../components/Form";
import MultiAutocompleteSelectField from "../../../components/MultiAutocompleteSelectField";
import Decorator from "../../Decorator";
import { ChoiceProvider } from "../../mock";

const suggestions = [
  "Afghanistan",
  "Burundi",
  "Comoros",
  "Egypt",
  "Equatorial Guinea",
  "Greenland",
  "Isle of Man",
  "Israel",
  "Italy",
  "United States",
  "Wallis and Futuna",
  "Zimbabwe"
].map(c => ({ label: c, value: c.toLocaleLowerCase().replace(/\s+/, "_") }));

storiesOf("Generics / MultiAutocompleteSelectField", module)
  .addDecorator(Decorator)
  .add("with loading data", () => (
    <Form initial={{ countries: [suggestions[0]] }}>
      {({ change, data }) => (
        <ChoiceProvider choices={suggestions}>
          {({ choices, fetchChoices }) => (
            <MultiAutocompleteSelectField
              choices={choices}
              fetchChoices={fetchChoices}
              helperText={`Value: ${data.countries.map(c => c.value)}`}
              loading={true}
              name="countries"
              onChange={change}
              placeholder="Select country"
              value={data.countries}
            />
          )}
        </ChoiceProvider>
      )}
    </Form>
  ))
  .add("with loaded data", () => (
    <Form initial={{ countries: [suggestions[0]] }}>
      {({ change, data }) => (
        <ChoiceProvider choices={suggestions}>
          {({ choices, fetchChoices }) => (
            <MultiAutocompleteSelectField
              choices={choices}
              fetchChoices={fetchChoices}
              helperText={`Value: ${data.countries.map(c => c.value)}`}
              loading={false}
              name="countries"
              onChange={change}
              placeholder="Select country"
              value={data.countries}
            />
          )}
        </ChoiceProvider>
      )}
    </Form>
  ));
