import React from "react";

const AppHeaderContext = React.createContext<React.RefObject<HTMLDivElement>>(
  undefined
);

export default AppHeaderContext;
