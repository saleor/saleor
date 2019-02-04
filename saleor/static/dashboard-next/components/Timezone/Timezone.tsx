import * as React from "react";

const {
  Consumer: TimezoneConsumer,
  Provider: TimezoneProvider
} = React.createContext<string>(undefined);

export { TimezoneConsumer, TimezoneProvider };
