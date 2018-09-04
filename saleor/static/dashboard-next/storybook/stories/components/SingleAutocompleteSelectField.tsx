import { storiesOf } from "@storybook/react";
import * as React from "react";

import Form from "../../../components/Form";
import SingleAutocompleteSelectField from "../../../components/SingleAutocompleteSelectField";
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

storiesOf("Generics / SingleAutocompleteSelectField", module)
  .addDecorator(Decorator)
  .add("with loading data", () => (
    <Form initial={{ country: suggestions[0] }}>
      {({ change, data }) => (
        <ChoiceProvider choices={suggestions}>
          {({ choices, fetchChoices }) => (
            <SingleAutocompleteSelectField
              choices={choices}
              fetchChoices={fetchChoices}
              helperText={`Value: ${data.country.value}`}
              loading={true}
              name="country"
              onChange={change}
              placeholder="Select country"
              value={data.country}
            />
          )}
        </ChoiceProvider>
      )}
    </Form>
  ))
  .add("with loaded data", () => (
    <Form initial={{ country: suggestions[0] }}>
      {({ change, data }) => (
        <ChoiceProvider choices={suggestions}>
          {({ choices, fetchChoices }) => (
            <SingleAutocompleteSelectField
              choices={choices}
              fetchChoices={fetchChoices}
              helperText={`Value: ${data.country.value}`}
              loading={false}
              name="country"
              onChange={change}
              placeholder="Select country"
              value={data.country}
            />
          )}
        </ChoiceProvider>
      )}
    </Form>
  ))
  .add("with custom option", () => (
    <Form initial={{ country: suggestions[0] }}>
      {({ change, data }) => (
        <ChoiceProvider choices={suggestions}>
          {({ choices, fetchChoices, loading }) => (
            <SingleAutocompleteSelectField
              choices={choices}
              custom={true}
              fetchChoices={fetchChoices}
              helperText={`Value: ${data.country.value}`}
              loading={loading}
              name="country"
              onChange={change}
              placeholder="Select country"
              value={data.country}
            />
          )}
        </ChoiceProvider>
      )}
    </Form>
  ));
