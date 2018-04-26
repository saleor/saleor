import * as React from "react";
import * as renderer from "react-test-renderer";

import OrderFilters from "./";

describe("<OrderFilters />", () => {
  it("renders", () => {
    const component = renderer.create(<OrderFilters />);
    expect(component).toMatchSnapshot();
  });
});
