import DeleteIcon from "material-ui-icons/Delete";
import IconButton from "material-ui/IconButton";
import * as React from "react";
import * as renderer from "react-test-renderer";

import PageHeader from "./";

describe("<PageHeader />", () => {
  it("renders without title", () => {
    const component = renderer.create(<PageHeader />);
    expect(component).toMatchSnapshot();
  });
  it("renders with title", () => {
    const component = renderer.create(<PageHeader title="Lorem ipsum" />);
    expect(component).toMatchSnapshot();
  });
  it("renders with title and back button", () => {
    const component = renderer.create(
      <PageHeader title="Lorem ipsum" onBack={jest.fn()} />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders with title icon bar", () => {
    const component = renderer.create(
      <PageHeader title="Lorem ipsum">
        <IconButton>
          <DeleteIcon />
        </IconButton>
      </PageHeader>
    );
    expect(component).toMatchSnapshot();
  });
  it("renders with title, back button and icon bar", () => {
    const component = renderer.create(
      <PageHeader title="Lorem ipsum" onBack={jest.fn()}>
        <IconButton>
          <DeleteIcon />
        </IconButton>
      </PageHeader>
    );
    expect(component).toMatchSnapshot();
  });
});
