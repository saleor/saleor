import * as React from "react";
import * as renderer from "react-test-renderer";

import CategoryList from "./CategoryList";

const categories = [
  {
    id: "cat1",
    name: "Apparel"
  },
  {
    id: "cat2",
    name: "Accessories"
  },
  {
    id: "cat3",
    name: "Groceries"
  },
  {
    id: "cat4",
    name: "Books"
  }
];

describe("<CategoryList />", () => {
  it("renders while data is loading", () => {
    const component = renderer.create(<CategoryList />);
    expect(component).toMatchSnapshot();
  });
  it("renders when data is fully loaded", () => {
    const component = renderer.create(
      <CategoryList categories={categories} onClick={jest.fn()} />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders when category list is empty", () => {
    const component = renderer.create(<CategoryList categories={[]} />);
    expect(component).toMatchSnapshot();
  });
});
