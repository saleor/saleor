import * as React from "react";

import i18n from "../../i18n";
import { LocaleConsumer } from "../Locale";
import IMoney from "../Money";

export interface MoneyRangeProps {
  from?: IMoney;
  to?: IMoney;
}

const formatMoney = (money: IMoney, locale: string) =>
  money.amount.toLocaleString(locale, {
    currency: money.currency,
    style: "currency"
  });

export const MoneyRange: React.StatelessComponent<MoneyRangeProps> = ({
  from,
  to
}) => (
  <LocaleConsumer>
    {locale =>
      from && to
        ? i18n.t("{{ fromMoney }} - {{ toMoney }}", {
            context: "money",
            fromMoney: formatMoney(from, locale),
            toMoney: formatMoney(to, locale)
          })
        : from && !to
        ? i18n.t("from {{ money }}", {
            context: "money",
            money: formatMoney(from, locale)
          })
        : !from && to
        ? i18n.t("to {{ money }}", {
            context: "money",
            money: formatMoney(to, locale)
          })
        : "-"
    }
  </LocaleConsumer>
);

MoneyRange.displayName = "MoneyRange";
export default MoneyRange;
