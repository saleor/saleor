import * as React from "react";
import { MemoryRouter } from "react-router-dom";
import * as renderer from "react-test-renderer";

import CategoryList from "./CategoryList";

const categories = [
  {
    node: {
      id: "cat1",
      name: "Apparel"
    }
  },
  {
    node: {
      id: "cat2",
      name: "Accessories"
    }
  },
  {
    node: {
      id: "cat3",
      name: "Groceries"
    }
  },
  {
    node: {
      id: "cat4",
      name: "Books"
    }
  }
];

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
        <CategoryList categories={categories} onClick={jest.fn()} />
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
