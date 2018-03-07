import * as React from "react";
import { MemoryRouter } from "react-router-dom";
import * as renderer from "react-test-renderer";

import { ListCard } from "../../components/cards";
import Table from "../../components/Table";

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

describe("<ListCard />", () => {
  it("displays properly", () => {
    const component = renderer.create(
      <MemoryRouter>
        <ListCard {...listCardProps} />
      </MemoryRouter>
    );
    const tree = component.toJSON();
    expect(tree).toMatchSnapshot();
  });
  it("displays children", () => {
    const component = renderer.create(
      <MemoryRouter>
        <ListCard {...listCardProps}>
          <b>test</b>
        </ListCard>
      </MemoryRouter>
    );
    const tree = component.toJSON();
    expect(tree).toMatchSnapshot();
  });
});
