import { storiesOf } from "@storybook/react";
import React from "react";

import Form from "@saleor/components/Form";
import SingleAutocompleteSelectField, {
  SingleAutocompleteSelectFieldProps
} from "@saleor/components/SingleAutocompleteSelectField";
import { maybe } from "@saleor/misc";
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

const props: SingleAutocompleteSelectFieldProps = {
  choices: undefined,
  displayValue: undefined,
  label: "Country",
  loading: false,
  name: "country",
  onChange: () => undefined,
  placeholder: "Select country"
};

const Story: React.FC<
  Partial<SingleAutocompleteSelectFieldProps>
> = storyProps => {
  const [displayValue, setDisplayValue] = React.useState(suggestions[0].label);

  return (
    <Form initial={{ country: suggestions[0].value }}>
      {({ change, data }) => (
        <ChoiceProvider choices={suggestions}>
          {({ choices, loading, fetchChoices }) => {
            const handleSelect = (event: React.ChangeEvent<any>) => {
              const value: string = event.target.value;
              const match = choices.find(choice => choice.value === value);
              const label = maybe(() => match.label, value);
              setDisplayValue(label);
              change(event);
            };

            return (
              <SingleAutocompleteSelectField
                {...props}
                displayValue={displayValue}
                choices={choices}
                fetchChoices={fetchChoices}
                helperText={`Value: ${data.country}`}
                onChange={handleSelect}
                value={data.country}
                loading={loading}
                {...storyProps}
              />
            );
          }}
        </ChoiceProvider>
      )}
    </Form>
  );
};

storiesOf("Generics / SingleAutocompleteSelectField", module)
  .addDecorator(CardDecorator)
  .addDecorator(Decorator)
  .add("with loaded data", () => <Story />)
  .add("with loading data", () => <Story loading={true} />)
  .add("with custom option", () => <Story allowCustomValues={true} />);
