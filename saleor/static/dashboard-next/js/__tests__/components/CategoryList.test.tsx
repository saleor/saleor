import * as React from "react";
import { MemoryRouter } from "react-router-dom";
import * as renderer from "react-test-renderer";

import CategoryList from "../../components/CategoryList";
import categoryListFixture from "./fixtures/categoryList";

describe("<CategoryList />", () => {
  it("renders while data is loading", () => {
    const component = renderer.create(
      <MemoryRouter>
        <CategoryList />
      </MemoryRouter>
    );
    expect(component).toMatchSnapshot();
  });
  it("renders when data is fully loaded", () => {
    const component = renderer.create(
      <MemoryRouter>
        <CategoryList categories={categoryListFixture} onClick={jest.fn()} />
      </MemoryRouter>
    );
    expect(component).toMatchSnapshot();
  });
  it("renders when category list is empty", () => {
    const component = renderer.create(
      <MemoryRouter>
        <CategoryList categories={[]} />
      </MemoryRouter>
    );
    expect(component).toMatchSnapshot();
  });
});
