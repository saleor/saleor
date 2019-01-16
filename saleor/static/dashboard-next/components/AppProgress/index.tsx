import * as React from "react";

import Toggle, { ToggleFuncs } from "../Toggle";

interface IAppProgressContext {
  value: boolean;
  funcs: ToggleFuncs;
}

export const AppProgressContext = React.createContext<IAppProgressContext>(
  undefined
);

export const AppProgressProvider: React.StatelessComponent<{}> = ({
  children
}) => (
  <Toggle>
    {(value, funcs) => (
      <AppProgressContext.Provider
        value={{
          funcs,
          value
        }}
      >
        {children}
      </AppProgressContext.Provider>
    )}
  </Toggle>
);

export const AppProgress = AppProgressContext.Consumer;
export default AppProgress;
