import * as React from "react";

import { LocaleConsumer } from "../Locale";

interface PercentProps {
  amount: number;
}

const Percent: React.StatelessComponent<PercentProps> = ({ amount }) => (
  <LocaleConsumer>
    {locale => {
      return (amount / 100).toLocaleString(locale, {
        maximumFractionDigits: 2,
        style: "percent"
      });
    }}
  </LocaleConsumer>
);
Percent.displayName = "Percent";
export default Percent;
