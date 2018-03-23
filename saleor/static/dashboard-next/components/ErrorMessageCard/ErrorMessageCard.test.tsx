import * as React from "react";
import * as renderer from "react-test-renderer";

import ErrorMessageCard from "./ErrorMessageCard";

describe("<ErrorMessageCard />", () => {
  it("renders properly", () => {
    const component = renderer.create(
      <ErrorMessageCard message="Things are terrible." />
    );
    expect(component).toMatchSnapshot();
  });
});
