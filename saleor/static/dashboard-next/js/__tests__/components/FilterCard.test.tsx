import * as React from "react";
import { MemoryRouter } from "react-router-dom";
import * as renderer from "react-test-renderer";

import FilterCard from "../../components/cards/FilterCard";

describe("<CategoryDetails />", () => {
  it("renders properly", () => {
    const component = renderer.create(<FilterCard handleClear={jest.fn()} />);
    expect(component).toMatchSnapshot();
  });
});
