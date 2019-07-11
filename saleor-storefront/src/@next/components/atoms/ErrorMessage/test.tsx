import { shallow } from "enzyme";
import "jest-styled-components";
import React from "react";

import { ErrorMessage } from ".";
import * as S from "./styles";
import { IProps } from "./types";

describe("<ErrorMessage />", () => {
  const ERRORS = [{ field: "Field", message: "Message" }];
  const DEFAULT_PROPS = {
    errors: ERRORS,
  };

  const renderErrorMessage = (props: IProps) =>
    shallow(<ErrorMessage {...props} />);

  it("exists", () => {
    const error = renderErrorMessage(DEFAULT_PROPS);

    expect(error.exists()).toEqual(true);
    expect(error.find(S.ErrorMessage)).toHaveLength(1);
  });

  it("shouldn't render if `errors` array is empty", () => {
    const error = renderErrorMessage({ errors: [] });

    expect(error.find(S.ErrorMessage)).toHaveLength(0);
  });

  it("should render each message from `errors`", () => {
    const errors = renderErrorMessage({
      errors: [...ERRORS, ...ERRORS],
    }).find(S.ErrorParagraph);

    expect(errors).toHaveLength(2);
    expect(errors.at(0).text()).toEqual("Message");
    expect(errors.at(1).text()).toEqual("Message");
  });
});
