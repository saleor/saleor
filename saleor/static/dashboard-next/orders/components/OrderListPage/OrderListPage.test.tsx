import * as React from "react";
import * as renderer from "react-test-renderer";

import OrderListPage from "./";

describe("<OrderListPage />", () => {
  it("renders", () => {
    const component = renderer.create(<OrderListPage />);
    expect(component).toMatchSnapshot();
  });
});
