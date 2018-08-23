import { withStyles } from "@material-ui/core/styles";
import Tooltip from "@material-ui/core/Tooltip";
import Typography, { TypographyProps } from "@material-ui/core/Typography";
import * as moment from "moment";
import * as React from "react";
import ReactMoment from "react-moment";

import { LocaleConsumer } from "../Locale";
import { Consumer } from "./DateContext";

interface DateFormatterProps {
  date: string;
  locale?: string;
  typographyProps?: TypographyProps;
}

const decorate = withStyles(theme => ({ root: { display: "inline" } }), {
  name: "DateFormatter"
});
const DateFormatter = decorate<DateFormatterProps>(
  ({ classes, date, typographyProps }) => {
    return (
      <LocaleConsumer>
        {locale => (
          <Consumer>
            {dateNow => (
              <Typography
                component="span"
                className={classes.root}
                {...typographyProps}
              >
                {/* <Tooltip
                  title={moment(date)
                    .locale(locale)
                    .toDate()
                    .toLocaleString()}
                >
                  <ReactMoment from={dateNow} locale={locale}>
                    {date}
                  </ReactMoment>
                </Tooltip> */}
                <Tooltip title={date}>
                  <span>{date}</span>
                </Tooltip>
              </Typography>
            )}
          </Consumer>
        )}
      </LocaleConsumer>
    );
  }
);
export default DateFormatter;
