import * as React from "react";
import * as renderer from "react-test-renderer";

import FilterCard from "../../components/FilterCard";

describe("<FilterCard />", () => {
  it("renders properly", () => {
    const component = renderer.create(<FilterCard handleClear={jest.fn()} />);
    expect(component).toMatchSnapshot();
  });
});
