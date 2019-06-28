import { storiesOf } from "@storybook/react";
import React from "react";

import MultiAutocompleteSelectField, {
  MultiAutocompleteSelectFieldProps
} from "@saleor/components/MultiAutocompleteSelectField";
import useMultiAutocomplete from "@saleor/hooks/useMultiAutocomplete";
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

const props: MultiAutocompleteSelectFieldProps = {
  choices: undefined,
  displayValues: [],
  label: "Country",
  loading: false,
  name: "country",
  onChange: () => undefined,
  placeholder: "Select country",
  value: undefined
};

const Story: React.FC<
  Partial<MultiAutocompleteSelectFieldProps>
> = storyProps => {
  const { change, data: countries } = useMultiAutocomplete([suggestions[0]]);

  return (
    <ChoiceProvider choices={suggestions}>
      {({ choices, loading, fetchChoices }) => (
        <MultiAutocompleteSelectField
          {...props}
          displayValues={countries}
          choices={choices}
          fetchChoices={fetchChoices}
          helperText={`Value: ${countries
            .map(country => country.label)
            .join(", ")}`}
          onChange={event => change(event, choices)}
          value={countries.map(country => country.value)}
          loading={loading}
          {...storyProps}
        />
      )}
    </ChoiceProvider>
  );
};

storiesOf("Generics / MultiAutocompleteSelectField", module)
  .addDecorator(CardDecorator)
  .addDecorator(Decorator)
  .add("with loaded data", () => <Story />)
  .add("with loading data", () => <Story loading={true} />)
  .add("with custom option", () => <Story allowCustomValues={true} />);
