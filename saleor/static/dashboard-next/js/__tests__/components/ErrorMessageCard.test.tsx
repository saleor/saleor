import * as React from "react";
import * as renderer from "react-test-renderer";

import ErrorMessageCard from "../../components/ErrorMessageCard";
import errorMessageFixture from "./fixtures/errorMessage";

describe("<ErrorMessageCard />", () => {
  it("renders properly", () => {
    const component = renderer.create(
      <ErrorMessageCard message={errorMessageFixture} />
    );
    expect(component).toMatchSnapshot();
  });
});
