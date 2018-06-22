import { withStyles } from "@material-ui/core/styles";
import Tooltip from "@material-ui/core/Tooltip";
import Typography, { TypographyProps } from "@material-ui/core/Typography";
import * as moment from "moment";
import * as React from "react";
import ReactMoment from "react-moment";

interface DateFormatterProps {
  date: string;
  dateNow?: number;
  inputFormat?: string;
  outputFormat?: string;
  showTooltip?: boolean;
  locale?: string;
  typographyProps?: TypographyProps;
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
    typographyProps
  }) => {
    return (
      <Typography
        component="span"
        className={classes.root}
        {...typographyProps}
      >
        {showTooltip && dateNow ? (
          <Tooltip
            title={moment(date)
              .toDate()
              .toLocaleString()}
          >
            {dateNow ? (
              <ReactMoment from={dateNow}>{date}</ReactMoment>
            ) : (
              <>
                {moment(date)
                  .toDate()
                  .toLocaleString()}
              </>
            )}
          </Tooltip>
        ) : (
          moment(date)
            .toDate()
            .toLocaleString()
        )}
      </Typography>
    );
  }
);
export default DateFormatter;
