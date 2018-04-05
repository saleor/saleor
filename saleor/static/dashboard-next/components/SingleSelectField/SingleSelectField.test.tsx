import * as React from "react";
import * as renderer from "react-test-renderer";

import SingleSelectField from "./";

const choices = [
  { value: "1", label: "Apparel" },
  { value: "2", label: "Groceries" },
  { value: "3", label: "Books" },
  { value: "4", label: "Accessories" }
];

describe("<MultiSelectField />", () => {
  it("renders with no value", () => {
    const component = renderer.create(
      <SingleSelectField choices={choices} onChange={() => {}} />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders with value", () => {
    const component = renderer.create(
      <SingleSelectField
        choices={choices}
        onChange={() => {}}
        value={choices[0].value}
      />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders with label", () => {
    const component = renderer.create(
      <SingleSelectField
        choices={choices}
        onChange={() => {}}
        label="Lorem ipsum"
      />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders with hint", () => {
    const component = renderer.create(
      <SingleSelectField
        choices={choices}
        onChange={() => {}}
        hint="Lorem ipsum"
      />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders with label and hint", () => {
    const component = renderer.create(
      <SingleSelectField
        choices={choices}
        onChange={() => {}}
        label="Lorem"
        hint="Ipsum"
      />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders with value, label and hint", () => {
    const component = renderer.create(
      <SingleSelectField
        choices={choices}
        onChange={() => {}}
        value={choices[0].value}
        label="Lorem"
        hint="Ipsum"
      />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders with error hint", () => {
    const component = renderer.create(
      <SingleSelectField
        choices={choices}
        onChange={() => {}}
        hint="Lorem error"
        error={true}
      />
    );
    expect(component).toMatchSnapshot();
  });
});
