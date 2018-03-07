import * as React from "react";
import { MemoryRouter } from "react-router-dom";
import * as renderer from "react-test-renderer";

import { CategoryListCard } from "../../category/details/CategoryListCard";

const listCardProps = {
  displayLabel: true,
  headers: [
    {
      name: "prop1",
      label: "Prop1"
    }
  ],
  list: [
    {
      prop1: "value1",
      prop2: "value2"
    }
  ],
  label: "Title",
  addActionLabel: "Add",
  addActionLink: "/link/"
};

describe("<CategoryListCard />", () => {
  it("displays properly", () => {
    const component = renderer.create(
      <MemoryRouter>
        <CategoryListCard {...listCardProps} />
      </MemoryRouter>
    );
    const tree = component.toJSON();
    expect(tree).toMatchSnapshot();
  });
  it("displays children", () => {
    const component = renderer.create(
      <MemoryRouter>
        <CategoryListCard {...listCardProps}>
          <b>test</b>
        </CategoryListCard>
      </MemoryRouter>
    );
    const tree = component.toJSON();
    expect(tree).toMatchSnapshot();
  });
});
