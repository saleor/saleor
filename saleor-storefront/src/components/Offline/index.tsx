import * as React from "react";

import NetworkStatus from "./";

const Offline: React.FC = ({ children }) => (
  <NetworkStatus>{online => (online ? null : children)}</NetworkStatus>
);

export default Offline;
