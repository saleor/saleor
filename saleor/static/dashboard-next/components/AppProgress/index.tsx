import React from "react";

interface IAppProgressContext {
  isProgress: boolean;
  setProgressState: (isOpened: boolean) => void;
}

export const AppProgressContext = React.createContext<IAppProgressContext>(
  undefined
);

export const AppProgressProvider: React.StatelessComponent<{}> = ({
  children
}) => {
  const [isProgress, setProgressState] = React.useState(false);

  return (
    <AppProgressContext.Provider
      value={{
        isProgress,
        setProgressState
      }}
    >
      {children}
    </AppProgressContext.Provider>
  );
};

export const AppProgress = AppProgressContext.Consumer;
export default AppProgress;
