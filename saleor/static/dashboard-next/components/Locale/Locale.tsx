import React from "react";

export const LocaleContext = React.createContext<string>("en");

const { Consumer: LocaleConsumer, Provider } = LocaleContext;

const LocaleProvider = ({ children }) => {
  return <Provider value={navigator.language}>{children}</Provider>;
};

export { LocaleConsumer, LocaleProvider };
