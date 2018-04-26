import * as React from "react";
import * as renderer from "react-test-renderer";

import PriceField, { PriceRangeField } from "./";

const value = {
  max: "30",
  min: "10"
};

describe("<PriceRangeField />", () => {
  it("renders with no value", () => {
    const component = renderer.create(<PriceRangeField onChange={() => {}} />);
    expect(component).toMatchSnapshot();
  });
  it("renders with value", () => {
    const component = renderer.create(
      <PriceRangeField value={value} onChange={() => {}} />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders with label", () => {
    const component = renderer.create(
      <PriceRangeField label="Lorem ipsum" onChange={() => {}} />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders with hint", () => {
    const component = renderer.create(
      <PriceRangeField hint="Lorem ipsum" onChange={() => {}} />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders with currency symbol", () => {
    const component = renderer.create(
      <PriceRangeField currencySymbol="$" onChange={() => {}} />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders when disabled", () => {
    const component = renderer.create(
      <PriceRangeField disabled onChange={() => {}} />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders with label and hint", () => {
    const component = renderer.create(
      <PriceRangeField label="Lorem" hint="Ipsum" onChange={() => {}} />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders with value, label and hint", () => {
    const component = renderer.create(
      <PriceRangeField
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
      <PriceRangeField
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

describe("<PriceField />", () => {
  it("renders with no value", () => {
    const component = renderer.create(<PriceField onChange={() => {}} />);
    expect(component).toMatchSnapshot();
  });
  it("renders with value", () => {
    const component = renderer.create(
      <PriceField value={"30"} onChange={() => {}} />
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
  it("renders with currency symbol", () => {
    const component = renderer.create(
      <PriceField currencySymbol="$" onChange={() => {}} />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders when disabled", () => {
    const component = renderer.create(
      <PriceField disabled onChange={() => {}} />
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
      <PriceField value={"30"} label="Lorem" hint="Ipsum" onChange={() => {}} />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders with value, label, currency symbol and error", () => {
    const component = renderer.create(
      <PriceField
        value={"30"}
        label="Lorem"
        hint="Ipsum"
        error={true}
        onChange={() => {}}
        currencySymbol="$"
      />
    );
    expect(component).toMatchSnapshot();
  });
});
