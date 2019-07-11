import { defaultTheme } from "@styles";
import { mount, shallow } from "enzyme";
import "jest-styled-components";
import React from "react";

import { Tile } from ".";

describe("<Tile />", () => {
  it("renders header, footer and content", () => {
    const headerText = "This is header";
    const contentText = "This is content";
    const footerText = "This is footer";

    const addHTMLSurroundingTag = (text: string) => <p>{text}</p>;

    const wrapper = shallow(
      <Tile
        header={addHTMLSurroundingTag(headerText)}
        footer={addHTMLSurroundingTag(footerText)}
      >
        {addHTMLSurroundingTag(contentText)}
      </Tile>
    );
    expect(wrapper.text()).toContain(headerText);
    expect(wrapper.text()).toContain(contentText);
    expect(wrapper.text()).toContain(footerText);
  });
  it("changes style on hover", () => {
    const wrapper = mount(
      <Tile>
        <p>This is content</p>
      </Tile>
    );

    const wrapperWithHover = mount(
      <Tile hover={true}>
        <p>This is content</p>
      </Tile>
    );

    expect(wrapper).not.toHaveStyleRule(
      "border-color",
      defaultTheme.tile.hoverBorder,
      {
        modifier: ":hover",
      }
    );

    expect(wrapperWithHover).toHaveStyleRule(
      "border-color",
      defaultTheme.tile.hoverBorder,
      {
        modifier: ":hover",
      }
    );
  });
});
