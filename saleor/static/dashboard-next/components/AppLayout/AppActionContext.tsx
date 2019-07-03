import React from "react";

const AppActionContext = React.createContext<React.RefObject<HTMLDivElement>>(
  undefined
);

export default AppActionContext;
