import * as React from "react";
import * as renderer from "react-test-renderer";

import PriceField from "./";

const value = {
  max: "30",
  min: "10"
};

describe("<PriceField />", () => {
  it("renders with no value", () => {
    const component = renderer.create(<PriceField onChange={() => {}} />);
    expect(component).toMatchSnapshot();
  });
  it("renders with value", () => {
    const component = renderer.create(
      <PriceField value={value} onChange={() => {}} />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders with label", () => {
    const component = renderer.create(
      <PriceField label="Lorem ipsum" onChange={() => {}} />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders with hint", () => {
    const component = renderer.create(
      <PriceField hint="Lorem ipsum" onChange={() => {}} />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders with label and hint", () => {
    const component = renderer.create(
      <PriceField label="Lorem" hint="Ipsum" onChange={() => {}} />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders with value, label and hint", () => {
    const component = renderer.create(
      <PriceField
        value={value}
        label="Lorem"
        hint="Ipsum"
        onChange={() => {}}
      />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders with value, label and error", () => {
    const component = renderer.create(
      <PriceField
        value={value}
        label="Lorem"
        hint="Ipsum"
        error={true}
        onChange={() => {}}
      />
    );
    expect(component).toMatchSnapshot();
  });
});
