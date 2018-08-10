import Typography, { TypographyProps } from "@material-ui/core/Typography";
import * as React from "react";

import { LocaleConsumer } from "../Locale";

interface PercentProps {
  amount: number;
  typographyProps?: TypographyProps;
}

const Percent: React.StatelessComponent<PercentProps> = ({
  amount,
  typographyProps
}) => (
  <LocaleConsumer>
    {locale => {
      const formattedAmount = (amount / 100).toLocaleString(locale, {
        maximumFractionDigits: 2,
        style: "percent"
      });
      if (typographyProps) {
        return <Typography {...typographyProps}>{formattedAmount}</Typography>;
      }
      return <>{formattedAmount}</>;
    }}
  </LocaleConsumer>
);
Percent.displayName = "Percent";
export default Percent;
