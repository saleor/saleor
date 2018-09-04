import { withStyles } from "@material-ui/core/styles";
import Tooltip from "@material-ui/core/Tooltip";
import Typography, { TypographyProps } from "@material-ui/core/Typography";
import * as React from "react";

interface DateFormatterProps {
  date: string;
  locale?: string;
  typographyProps?: TypographyProps;
}

const decorate = withStyles(
  { root: { display: "inline" } },
  {
    name: "DateFormatter"
  }
);
const DateFormatter = decorate<DateFormatterProps>(
  ({ classes, date, typographyProps }) => {
    return (
      <Typography
        component="span"
        className={classes.root}
        {...typographyProps}
      >
        <Tooltip title={date}>
          <span>{date}</span>
        </Tooltip>
      </Typography>
    );
  }
);
export default DateFormatter;
