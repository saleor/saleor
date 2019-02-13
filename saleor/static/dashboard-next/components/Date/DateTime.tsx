import * as React from "react";

import { TimezoneConsumer } from "../Timezone";
import BaseDate from "./BaseDate";

interface DateTimeProps {
  date: string;
  plain?: boolean;
}

export const DateTime: React.StatelessComponent<DateTimeProps> = props => (
  <TimezoneConsumer>
    {tz => <BaseDate {...props} format="lll" tz={tz} />}
  </TimezoneConsumer>
);
DateTime.displayName = "DateTime";
export default DateTime;
