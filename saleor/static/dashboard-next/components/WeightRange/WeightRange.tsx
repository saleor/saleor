import * as React from "react";

import i18n from "../../i18n";
import { Weight } from "../Weight";

export interface WeightRangeProps {
  from?: Weight;
  to?: Weight;
}

const WeightRange: React.StatelessComponent<WeightRangeProps> = ({
  from,
  to
}) =>
  from && to
    ? i18n.t("{{ fromValue }} {{ fromUnit }} - {{ toValue }} {{ toUnit }}", {
        context: "weight",
        fromUnit: from.unit,
        fromValue: from.value,
        toUnit: to.unit,
        toValue: to.value
      })
    : from && !to
    ? i18n.t("from {{ value }} {{ unit }}", {
        context: "weight",
        ...from
      })
    : !from && to
    ? i18n.t("to {{ value }} {{ unit }}", {
        context: "weight",
        ...to
      })
    : "-";
WeightRange.displayName = "WeightRange";
export default WeightRange;
