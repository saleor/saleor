import "./scss/accountNavigation.scss";

import React from "react";
import TabTitle from "./TabTitle";

export interface IAccountNavigation {
  links: string[];
  active: string;
}

const AccountNavigation: React.FC<IAccountNavigation> = ({ links, active }) => (
  <div className="account-navigation">
    {links.map(element => (
      <TabTitle key={element} element={element} active={active} />
    ))}
  </div>
);

export default AccountNavigation;
