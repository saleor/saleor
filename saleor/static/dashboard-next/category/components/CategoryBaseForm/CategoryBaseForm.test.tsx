import * as React from "react";
import { MemoryRouter } from "react-router-dom";
import * as renderer from "react-test-renderer";

import CategoryBaseForm from "./CategoryBaseForm";

const category = {
  description:
    "Across pressure PM food discover recognize. Send letter reach listen. Quickly work plan rule.\nTell lose part purpose do when. Whatever drug contain particularly defense.",
  name: "Apparel"
};
const errors = [
  {
    field: "name",
    message: "To pole jest wymagane."
  }
];

describe("<CategoryBaseForm />", () => {
  it("renders with initial data", () => {
    const component = renderer.create(<CategoryBaseForm {...category} />);
    expect(component).toMatchSnapshot();
  });
  it("renders without initial data", () => {
    const component = renderer.create(
      <MemoryRouter>
        <CategoryBaseForm />
      </MemoryRouter>
    );
    expect(component).toMatchSnapshot();
  });
  it("renders when errors occured", () => {
    const component = renderer.create(
      <CategoryBaseForm {...category} errors={errors} />
    );
    expect(component).toMatchSnapshot();
  });
});
