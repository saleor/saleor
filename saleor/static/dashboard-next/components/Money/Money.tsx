import * as React from "react";

import { LocaleConsumer } from "../Locale";

export interface IMoney {
  amount: number;
  currency: string;
}
export interface MoneyProps {
  money: IMoney;
}

export const Money: React.StatelessComponent<MoneyProps> = ({ money }) => (
  <LocaleConsumer>
    {locale => {
      return money.amount.toLocaleString(locale, {
        currency: money.currency,
        style: "currency"
      });
    }}
  </LocaleConsumer>
);

Money.displayName = "Money";
export default Money;
