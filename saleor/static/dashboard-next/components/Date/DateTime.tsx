import * as React from "react";

import BaseDate from "./BaseDate";

interface DateTimeProps {
  date: string;
  plain?: boolean;
}

export const DateTime: React.StatelessComponent<DateTimeProps> = props => (
  <BaseDate {...props} format="lll" />
);
DateTime.displayName = "DateTime";
export default DateTime;
