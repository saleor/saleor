import * as React from "react";

import DateComponent from "./DateComponent";

interface DateProps {
  date: string;
  plain?: boolean;
}

export const Date: React.StatelessComponent<DateProps> = props => (
  <DateComponent {...props} format="ll" />
);
Date.displayName = "Date";
export default Date;
