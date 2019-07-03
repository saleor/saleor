import IconButton from "@material-ui/core/IconButton";
import Typography from "@material-ui/core/Typography";
import DeleteIcon from "@material-ui/icons/Close";
import { storiesOf } from "@storybook/react";
import React from "react";

import Form from "@saleor/components/Form";
import MultiAutocompleteSelectField, {
  MultiAutocompleteSelectFieldChildrenFunc
} from "@saleor/components/MultiAutocompleteSelectField";
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

const Choices: React.FC<MultiAutocompleteSelectFieldChildrenFunc> = ({
  deleteItem,
  items
}) => (
  <div style={{ marginTop: 16 }}>
    {items.map(item => (
      <div
        style={{
          alignItems: "center",
          display: "flex",
          justifyContent: "space-between"
        }}
        key={item.value}
      >
        <Typography>{item.label}</Typography>
        <div
          style={{
            flex: 1
          }}
        />
        <IconButton onClick={() => deleteItem(item)}>
          <DeleteIcon style={{ fontSize: 16 }} />
        </IconButton>
      </div>
    ))}
  </div>
);

storiesOf("Generics / MultiAutocompleteSelectField", module)
  .addDecorator(CardDecorator)
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
              label="Countries"
              loading={true}
              name="countries"
              onChange={change}
              placeholder="Select country"
              value={data.countries}
            >
              {selectInput => <Choices {...selectInput} />}
            </MultiAutocompleteSelectField>
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
              label="Countries"
              loading={false}
              name="countries"
              onChange={change}
              placeholder="Select country"
              value={data.countries}
            >
              {selectInput => <Choices {...selectInput} />}
            </MultiAutocompleteSelectField>
          )}
        </ChoiceProvider>
      )}
    </Form>
  ));
