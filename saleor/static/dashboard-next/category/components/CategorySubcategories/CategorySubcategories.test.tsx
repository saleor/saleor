import * as React from "react";
import { MemoryRouter } from "react-router-dom";
import * as renderer from "react-test-renderer";

import CategorySubcategories from "./CategorySubcategories";

describe("<CategorySubcategories />", () => {
  it("renders with initial data", () => {
    const categories = [
      {
        id: "123123",
        name: "Lorem ipsum dolor"
      },
      {
        id: "876752",
        name: "Mauris vehicula tortor vulputate"
      }
    ];
    const component = renderer.create(
      <CategorySubcategories
        subcategories={categories}
        onClickSubcategory={jest.fn()}
        onCreate={jest.fn()}
      />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders without initial data", () => {
    const component = renderer.create(
      <CategorySubcategories
        subcategories={[]}
        onClickSubcategory={jest.fn()}
        onCreate={jest.fn()}
      />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders when loading data", () => {
    const component = renderer.create(
      <CategorySubcategories
        onClickSubcategory={jest.fn()}
        onCreate={jest.fn()}
      />
    );
    expect(component).toMatchSnapshot();
  });
});
