import * as React from "react";
import { MemoryRouter } from "react-router-dom";
import * as renderer from "react-test-renderer";

import CategoryPropertiesCard from "./CategoryPropertiesCard";

describe("<CategoryPropertiesCard />", () => {
  it("renders while data is loading", () => {
    const component = renderer.create(
      <MemoryRouter>
        <CategoryPropertiesCard description="" onDelete={jest.fn()} title="" />
      </MemoryRouter>
    );
    expect(component).toMatchSnapshot();
  });
  it("renders when data is loaded", () => {
    const component = renderer.create(
      <MemoryRouter>
        <CategoryPropertiesCard
          description="These are the best shoes."
          onDelete={jest.fn()}
          onEdit={jest.fn()}
          title="Shoes"
        />
      </MemoryRouter>
    );
    expect(component).toMatchSnapshot();
  });
});
