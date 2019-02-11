import * as React from "react";

import BaseDate from "./BaseDate";

interface DateProps {
  date: string;
  plain?: boolean;
}

export const Date: React.StatelessComponent<DateProps> = props => (
  <BaseDate {...props} format="ll" />
);
Date.displayName = "Date";
export default Date;
