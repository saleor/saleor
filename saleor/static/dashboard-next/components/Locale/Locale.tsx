import * as React from "react";

const { Consumer: LocaleConsumer, Provider } = React.createContext<string>(
  "en"
);

const LocaleProvider = ({ children }) => {
  return <Provider value={navigator.language}>{children}</Provider>;
};

export { LocaleConsumer, LocaleProvider };
