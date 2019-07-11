import { shallow } from "enzyme";
import "jest-styled-components";
import React from "react";
import ReactSVG from "react-svg";

import { CreditCardIcon } from ".";

describe("<CreditCardIcon />", () => {
  it("contains ReactSVG", () => {
    const wrapper = shallow(<CreditCardIcon provider="visa" />);
    expect(wrapper.exists(ReactSVG)).toBe(true);
  });
});
