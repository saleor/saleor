import Typography from "@material-ui/core/Typography";
import { storiesOf } from "@storybook/react";
import * as React from "react";

import FetchableAutocompleteField from "../../../components/FetchableAutocompleteField";
import Form from "../../../components/Form";
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
].map(c => ({ name: c, value: c.toLocaleLowerCase().replace(/\s+/, "_") }));

storiesOf("Generics / Autocomplete select field with fetch", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <Form initial={{ country: suggestions[0].value }}>
      {({ change, data }) => (
        <ChoiceProvider choices={suggestions}>
          {({ choices, fetchChoices, loading }) => (
            <FetchableAutocompleteField
              loading={loading}
              choices={choices}
              helperText={`Value: ${data.country}`}
              name="country"
              onChange={change}
              placeholder="Select country"
              value={data.country}
              fetchChoices={fetchChoices}
            />
          )}
        </ChoiceProvider>
      )}
    </Form>
  ));
