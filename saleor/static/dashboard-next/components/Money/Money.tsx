import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

interface MoneyProps {
  amount: number;
  currency: string;
}

const decorate = withStyles(theme => ({
  currency: {
    color: theme.palette.grey[500]
  }
}));
const Money = decorate<MoneyProps>(({ classes, amount, currency }) => (
  <Typography>
    {amount.toFixed(2)} <span className={classes.currency}>{currency}</span>
  </Typography>
));
export default Money;
