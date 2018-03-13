import * as React from "react";
import { MemoryRouter } from "react-router-dom";
import * as renderer from "react-test-renderer";

import { CategoryDetails } from "../../category/components/CategoryDetails";
import categoryListFixture from "./fixtures/categoryList";
import categoryFixture from "./fixtures/category";

describe("<CategoryDetails />", () => {
  it("renders while data is loading", () => {
    const component = renderer.create(
      <MemoryRouter>
        <CategoryDetails
          description=""
          editButtonLink=""
          loading={false}
          title=""
          handleRemoveButtonClick={jest.fn()}
        />
      </MemoryRouter>
    );
    expect(component).toMatchSnapshot();
  });
  it("renders when data is loaded", () => {
    const component = renderer.create(
      <MemoryRouter>
        <CategoryDetails
          description={categoryFixture.node.description}
          editButtonLink={`/categories/${categoryFixture.node.id}/edit/`}
          loading={false}
          title={categoryFixture.node.name}
          handleRemoveButtonClick={jest.fn()}
        />
      </MemoryRouter>
    );
    expect(component).toMatchSnapshot();
  });
});
