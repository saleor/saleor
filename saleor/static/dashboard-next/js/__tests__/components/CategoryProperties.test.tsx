import * as React from "react";
import { MemoryRouter } from "react-router-dom";
import * as renderer from "react-test-renderer";

import CategoryProperties from "../../category/components/CategoryProperties";
import categoryFixture from "./fixtures/category";
import categoryListFixture from "./fixtures/categoryList";

describe("<CategoryProperties />", () => {
  it("renders while data is loading", () => {
    const component = renderer.create(
      <MemoryRouter>
        <CategoryProperties description="" onDelete={jest.fn()} title="" />
      </MemoryRouter>
    );
    expect(component).toMatchSnapshot();
  });
  it("renders when data is loaded", () => {
    const component = renderer.create(
      <MemoryRouter>
        <CategoryProperties
          description={categoryFixture.node.description}
          onDelete={jest.fn()}
          onEdit={jest.fn()}
          title={categoryFixture.node.name}
        />
      </MemoryRouter>
    );
    expect(component).toMatchSnapshot();
  });
});
