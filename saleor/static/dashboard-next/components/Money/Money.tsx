import Typography, { TypographyProps } from "@material-ui/core/Typography";
import * as React from "react";

import { LocaleConsumer } from "../Locale";

interface MoneyProps {
  amount: number;
  currency: string;
  typographyProps?: TypographyProps;
}

export const Money: React.StatelessComponent<MoneyProps> = ({
  amount,
  currency,
  typographyProps
}) => (
  <LocaleConsumer>
    {locale => {
      const money = amount.toLocaleString(locale, {
        currency,
        style: "currency"
      });
      if (typographyProps) {
        return <Typography {...typographyProps}>{money}</Typography>;
      }
      return <>{money}</>;
    }}
  </LocaleConsumer>
);

export default Money;
