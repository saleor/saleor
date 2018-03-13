import * as React from "react";
import { MemoryRouter } from "react-router-dom";
import * as renderer from "react-test-renderer";

import { CategoryChildElement } from "../../category/components/CategoryChildElement";
import categoryListFixture from "./fixtures/categoryList";

const categoryFixture = categoryListFixture[0];

describe("<ProductChildElement />", () => {
  it("renders while data is loading", () => {
    const component = renderer.create(
      <MemoryRouter>
        <CategoryChildElement label="" url="" loading={true} />
      </MemoryRouter>
    );
    expect(component).toMatchSnapshot();
  });
  it("renders when data is loaded", () => {
    const component = renderer.create(
      <MemoryRouter>
        <CategoryChildElement
          label={categoryFixture.node.name}
          url={`/categories/${categoryFixture.node.id}/`}
          loading={false}
        />
      </MemoryRouter>
    );
    expect(component).toMatchSnapshot();
  });
});
