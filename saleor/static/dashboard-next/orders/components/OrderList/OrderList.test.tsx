import * as React from "react";
import * as renderer from "react-test-renderer";

import OrderList from "./";

describe("<OrderList />", () => {
  it("renders", () => {
    const component = renderer.create(<OrderList />);
    expect(component).toMatchSnapshot();
  });
});
