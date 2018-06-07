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
    const momentDate = inputFormat ? moment(date, inputFormat) : moment(date);
    if (!dateNow || moment(dateNow).diff(momentDate, "days") > 1) {
      return (
        <Typography
          className={classes.root}
          variant={(typography as any) || "body1"}
        >
          {momentDate.format(outputFormat || "DD.MM.YYYY HH:mm")}
        </Typography>
      );
    }
    if (showTooltip) {
      return (
        <Tooltip
          title={momentDate.format(outputFormat || "DD.MM.YYYY HH:mm")}
          placement="bottom"
        >
          <Typography className={classes.root}>
            {locale
              ? momentDate.locale(locale).fromNow()
              : momentDate.fromNow()}
          </Typography>
        </Tooltip>
      );
    }
    return (
      <Typography className={classes.root}>
        {locale ? momentDate.locale(locale).fromNow() : momentDate.fromNow()}
      </Typography>
    );
  }
);
export default DateFormatter;
