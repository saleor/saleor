import Typography from "@material-ui/core/Typography";
import { storiesOf } from "@storybook/react";
import * as React from "react";

import Form from "../../../components/Form";
import SingleAutocompleteField from "../../../components/SingleAutocompleteField";
import Decorator from "../../Decorator";

const choices = [
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
].map(c => ({ name: c, value: c.toLocaleLowerCase().replace(/\s+/, "_") }));

storiesOf("Generics / Autocomplete select field", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <Form initial={{ country: choices[0].value }}>
      {({ change, data }) => (
        <SingleAutocompleteField
          choices={choices}
          helperText={`Value: ${data.country}`}
          name="country"
          onChange={change}
          placeholder="Select country"
          initialLabel={choices[0].name}
          value={data.country}
        />
      )}
    </Form>
  ))
  .add("sortable", () => (
    <Form initial={{ country: choices[0].value }}>
      {({ change, data }) => (
        <SingleAutocompleteField
          choices={choices}
          helperText={`Value: ${data.country}`}
          name="country"
          onChange={change}
          placeholder="Select country"
          sort={true}
          initialLabel={choices[0].name}
          value={data.country}
        />
      )}
    </Form>
  ))
  .add("custom labels", () => (
    <Form initial={{ country: choices[0].value }}>
      {({ change, data }) => (
        <SingleAutocompleteField
          choices={choices.map(choice => ({
            ...choice,
            label: <Typography variant="caption">{choice.name}</Typography>
          }))}
          helperText={`Value: ${data.country}`}
          name="country"
          onChange={change}
          placeholder="Select country"
          sort={true}
          initialLabel={choices[0].name}
          value={data.country}
        />
      )}
    </Form>
  ));
