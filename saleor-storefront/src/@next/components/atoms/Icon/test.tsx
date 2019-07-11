import { shallow } from "enzyme";
import React from "react";

import { Icon } from ".";

describe("<Icon />", () => {
  it("renders an icon", () => {
    const wrapper = shallow(<Icon name="arrow_back" />);

    expect(wrapper.find("path").exists()).toEqual(true);
  });
});
