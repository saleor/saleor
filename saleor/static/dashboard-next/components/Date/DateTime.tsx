import * as React from "react";

import DateComponent from "./DateComponent";

interface DateTimeProps {
  date: string;
  plain?: boolean;
}

export const DateTime: React.StatelessComponent<DateTimeProps> = props => (
  <DateComponent {...props} format="lll" />
);
DateTime.displayName = "DateTime";
export default DateTime;
