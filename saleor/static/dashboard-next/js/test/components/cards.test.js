import React from "react";
import Enzyme, { shallow } from "enzyme";
import { expect } from "chai";
import Adapter from "enzyme-adapter-react-15";

import { ListCardComponent, CardTitle } from "../../components/cards";
import Table from "../../components/Table";

Enzyme.configure({ adapter: new Adapter() });

const listCardProps = {
  displayLabel: true,
  headers: [
    {
      name: "prop1",
      label: "Prop1"
    }
  ],
  list: [
    {
      prop1: "value1",
      prop2: "value2"
    }
  ],
  // firstCursor,
  // lastCursor,
  classes: {},
  handleChangePage: () => {},
  handleChangeRowsPerPage: () => {},
  page: 0,
  rowsPerPage: 5,
  label: "Title",
  addActionLabel: "Add",
  noDataLabel: "No data"
};

describe("<ListCard />", () => {
  it("displays title when allowed to", () => {
    const wrapper = shallow(<ListCardComponent {...listCardProps} />);
    expect(wrapper.find(CardTitle)).to.have.length(1);
  });
  it("does not display title when not allowed to", () => {
    const componentProps = Object.assign({}, listCardProps, {
      displayLabel: false
    });
    const wrapper = shallow(<ListCardComponent {...componentProps} />);
    expect(wrapper.find(CardTitle)).to.have.length(0);
  });
  it("displays table", () => {
    const wrapper = shallow(<ListCardComponent {...listCardProps} />);
    expect(wrapper.find(Table)).to.have.length(1);
  });
});

describe("<DescriptionCard />", () => {
  it("");
});
