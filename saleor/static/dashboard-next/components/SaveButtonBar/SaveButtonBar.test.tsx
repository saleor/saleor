import * as React from "react";
import * as renderer from "react-test-renderer";

import SaveButtonBar from "./SaveButtonBar";

describe("<SaveButtonBar />", () => {
  it("renders", () => {
    const component = renderer.create(
      <SaveButtonBar onBack={jest.fn()} onSave={jest.fn()} />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders when disabled", () => {
    const component = renderer.create(
      <SaveButtonBar onBack={jest.fn()} onSave={jest.fn()} disabled />
    );
    expect(component).toMatchSnapshot();
  });
});
