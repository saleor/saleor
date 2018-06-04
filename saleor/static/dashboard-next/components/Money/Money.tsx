import grey from "material-ui/colors/grey";
import { withStyles } from "material-ui/styles";
import Typography from "material-ui/Typography";
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
