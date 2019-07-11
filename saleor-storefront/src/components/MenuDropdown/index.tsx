import * as React from "react";

import "./scss/index.scss";

class MenuDropdown extends React.Component<
  {
    head: React.ReactElement<{}>;
    content: React.ReactElement<{}>;
  },
  { active: boolean }
> {
  constructor(props) {
    super(props);
    this.state = { active: false };
  }
  render() {
    return (
      <div
        data-testid="user-btn"
        className="menu-dropdown"
        onMouseOver={() => this.setState({ active: true })}
        onMouseLeave={() => this.setState({ active: false })}
      >
        {this.props.head}

        <div
          className={`menu-dropdown__body${
            this.state.active ? " menu-dropdown__body--visible" : ""
          }`}
        >
          {this.props.content}
        </div>
      </div>
    );
  }
}

export default MenuDropdown;
