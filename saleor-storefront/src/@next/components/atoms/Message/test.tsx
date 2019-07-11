import { defaultTheme } from "@styles";
import { mount, shallow } from "enzyme";
import "jest-styled-components";
import React from "react";

import { Message } from ".";
import { Title } from "./styles";

describe("<Message />", () => {
  it("renders passed title", () => {
    const text = "test";
    const wrapper = shallow(<Message title={text} onClick={jest.fn()} />);

    expect(wrapper.find(Title).text()).toEqual(text);
  });

  it("renders children when passed in", () => {
    const wrapper = shallow(
      <Message title="" onClick={jest.fn()}>
        <div className="unique" />
      </Message>
    );

    expect(wrapper.contains(<div className="unique" />)).toEqual(true);
  });

  it("displays correct border color based on status prop", () => {
    const neutral = mount(<Message title="" onClick={jest.fn()} />);
    const success = mount(
      <Message title="" onClick={jest.fn()} status="success" />
    );
    const error = mount(
      <Message title="" onClick={jest.fn()} status="error" />
    );

    expect(neutral).toHaveStyleRule(
      "border-color",
      defaultTheme.colors.primaryDark
    );
    expect(success).toHaveStyleRule(
      "border-color",
      defaultTheme.colors.success
    );
    expect(error).toHaveStyleRule("border-color", defaultTheme.colors.error);
  });
});
