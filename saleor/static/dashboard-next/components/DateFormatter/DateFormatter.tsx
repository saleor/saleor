import { withStyles } from "@material-ui/core/styles";
import Tooltip from "@material-ui/core/Tooltip";
import Typography from "@material-ui/core/Typography";
import * as moment from "moment";
import * as React from "react";

interface DateFormatterProps {
  date: string;
  dateNow?: number;
  inputFormat?: string;
  outputFormat?: string;
  showTooltip?: boolean;
  locale?: string;
  typography?: string;
}

const decorate = withStyles(theme => ({ root: { display: "inline" } }), {
  name: "DateFormatter"
});
const DateFormatter = decorate<DateFormatterProps>(
  ({
    classes,
    date,
    dateNow,
    inputFormat,
    outputFormat,
    showTooltip = true,
    locale,
    typography
  }) => {
    return <span>{date}</span>;
  }
);
export default DateFormatter;
