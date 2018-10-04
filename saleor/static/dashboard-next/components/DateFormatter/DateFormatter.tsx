import Tooltip from "@material-ui/core/Tooltip";
import * as React from "react";

interface DateFormatterProps {
  date: string;
  locale?: string;
}

const DateFormatter: React.StatelessComponent<DateFormatterProps> = ({
  date
}) => (
  <Tooltip title={date}>
    <span>{date}</span>
  </Tooltip>
);
export default DateFormatter;
