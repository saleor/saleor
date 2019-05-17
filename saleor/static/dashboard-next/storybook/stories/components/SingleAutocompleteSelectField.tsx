import { storiesOf } from "@storybook/react";
import * as React from "react";

import Form from "../../../components/Form";
import SingleAutocompleteSelectField from "../../../components/SingleAutocompleteSelectField";
import CardDecorator from "../../CardDecorator";
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

const props = {
  label: "Country",
  loading: false,
  name: "country",
  placeholder: "Select country"
};

storiesOf("Generics / SingleAutocompleteSelectField", module)
  .addDecorator(CardDecorator)
  .addDecorator(Decorator)
  .add("with loading data", () => (
    <Form initial={{ country: suggestions[0] }}>
      {({ change, data }) => (
        <ChoiceProvider choices={suggestions}>
          {({ choices, fetchChoices }) => (
            <SingleAutocompleteSelectField
              {...props}
              choices={choices}
              fetchChoices={fetchChoices}
              helperText={`Value: ${data.country.value}`}
              loading={true}
              onChange={change}
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
              {...props}
              choices={choices}
              fetchChoices={fetchChoices}
              helperText={`Value: ${data.country.value}`}
              onChange={change}
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
              {...props}
              choices={choices}
              fetchChoices={fetchChoices}
              helperText={`Value: ${data.country.value}`}
              loading={loading}
              onChange={change}
              value={data.country}
              custom={true}
            />
          )}
        </ChoiceProvider>
      )}
    </Form>
  ));
