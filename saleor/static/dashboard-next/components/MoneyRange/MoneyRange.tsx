import * as React from "react";

import i18n from "../../i18n";
import { LocaleConsumer } from "../Locale";
import IMoney from "../Money";

export interface MoneyRangeProps {
  from?: IMoney;
  to?: IMoney;
}

export const MoneyRange: React.StatelessComponent<MoneyRangeProps> = ({
  from,
  to
}) => (
  <LocaleConsumer>
    {locale =>
      from && to
        ? i18n.t("{{ fromMoney }} - {{ toMoney }}", {
            context: "money",
            fromMoney: from.amount.toLocaleString(locale, {
              currency: from.currency,
              style: "currency"
            }),
            toMoney: to.amount.toLocaleString(locale, {
              currency: to.currency,
              style: "currency"
            })
          })
        : from && !to
        ? i18n.t("from {{ money }}", {
            context: "money",
            money: from.amount.toLocaleString(locale, {
              currency: from.currency,
              style: "currency"
            })
          })
        : i18n.t("to {{ money }}", {
            context: "money",
            money: to.amount.toLocaleString(locale, {
              currency: to.currency,
              style: "currency"
            })
          })
    }
  </LocaleConsumer>
);

MoneyRange.displayName = "MoneyRange";
export default MoneyRange;
