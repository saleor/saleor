import * as React from "react";
import * as renderer from "react-test-renderer";

import PageFilters from "./";

const pageFilters = {
  title: "title",
  url: "url"
};

describe("<PageFilters />", () => {
  it("renders without initial state", () => {
    const component = renderer.create(
      <PageFilters handleClear={jest.fn()} handleSubmit={jest.fn()} />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders with initial state", () => {
    const component = renderer.create(
      <PageFilters
        formState={pageFilters}
        handleClear={jest.fn()}
        handleSubmit={jest.fn()}
      />
    );
    expect(component).toMatchSnapshot();
  });
});
