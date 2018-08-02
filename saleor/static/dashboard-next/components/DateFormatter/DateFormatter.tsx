import { withStyles } from "@material-ui/core/styles";
import Tooltip from "@material-ui/core/Tooltip";
import Typography, { TypographyProps } from "@material-ui/core/Typography";
import * as moment from "moment";
import * as React from "react";
import ReactMoment from "react-moment";

import { LocaleConsumer } from "../Locale";
import { Consumer } from "./DateContext";

interface DateFormatterProps {
  date: number;
  showTooltip?: boolean;
  locale?: string;
  typographyProps?: TypographyProps;
}

const decorate = withStyles(theme => ({ root: { display: "inline" } }), {
  name: "DateFormatter"
});
const DateFormatter = decorate<DateFormatterProps>(
  ({ classes, date, showTooltip = true, typographyProps }) => {
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
                {showTooltip ? (
                  <Tooltip
                    title={moment(date)
                      .toDate()
                      .toLocaleString()}
                  >
                    <ReactMoment from={dateNow} locale={locale}>
                      {date}
                    </ReactMoment>
                  </Tooltip>
                ) : (
                  <ReactMoment from={dateNow} locale={locale}>
                    {date}
                  </ReactMoment>
                )}
              </Typography>
            )}
          </Consumer>
        )}
      </LocaleConsumer>
    );
  }
);
export default DateFormatter;
