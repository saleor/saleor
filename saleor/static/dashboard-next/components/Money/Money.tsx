import { withStyles } from "@material-ui/core/styles";
import Typography, { TypographyProps } from "@material-ui/core/Typography";
import * as React from "react";

interface MoneyProps {
  amount: number;
  currency: string;
  typographyProps?: TypographyProps;
}

const decorate = withStyles(theme => ({
  currency: {
    color: theme.palette.grey[500]
  }
}));
const Money = decorate<MoneyProps>(
  ({ classes, amount, currency, typographyProps }) => (
    <Typography {...typographyProps}>
      {amount.toFixed(2)} <span className={classes.currency}>{currency}</span>
    </Typography>
  )
);
export default Money;
