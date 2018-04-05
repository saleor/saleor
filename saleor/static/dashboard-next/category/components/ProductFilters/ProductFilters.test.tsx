import * as React from "react";
import * as renderer from "react-test-renderer";

import ProductFilters from "./";

const productTypes = [
  { id: "123123123", name: "Type 1" },
  { id: "123123124", name: "Type 2" },
  { id: "123123125", name: "Type 3" },
  { id: "123123126", name: "Type 4" }
];
const productFilters = {
  highlighted: "false",
  name: "Lorem ipsum",
  price_max: "50",
  price_min: "30",
  productTypes: ["123123123", "123123126"],
  published: "true"
};

describe("<ProductFilters />", () => {
  it("renders without initial state", () => {
    const component = renderer.create(
      <ProductFilters
        handleClear={jest.fn()}
        handleSubmit={jest.fn()}
        productTypes={productTypes}
      />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders with initial state", () => {
    const component = renderer.create(
      <ProductFilters
        formState={productFilters}
        handleClear={jest.fn()}
        handleSubmit={jest.fn()}
        productTypes={productTypes}
      />
    );
    expect(component).toMatchSnapshot();
  });
});
