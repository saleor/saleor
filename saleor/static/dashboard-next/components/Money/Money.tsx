import * as React from "react";

import { LocaleConsumer } from "../Locale";

export interface Money {
  amount: number;
  currency: string;
}
export interface MoneyProps {
  money: Money;
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

export default Money;
