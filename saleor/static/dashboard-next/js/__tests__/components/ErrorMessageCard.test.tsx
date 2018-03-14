import * as React from "react";
import { MemoryRouter } from "react-router-dom";
import * as renderer from "react-test-renderer";

import ErrorMessageCard from "../../components/cards/ErrorMessageCard";
import errorMessageFixture from "./fixtures/errorMessage";

describe("<ProductChildElement />", () => {
  it("renders properly", () => {
    const component = renderer.create(
      <ErrorMessageCard message={errorMessageFixture} />
    );
    expect(component).toMatchSnapshot();
  });
});
