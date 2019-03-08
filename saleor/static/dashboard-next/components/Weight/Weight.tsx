import * as React from "react";
import i18n from "../../i18n";

export interface Weight {
  unit: string;
  value: number;
}
export interface WeightProps {
  weight: Weight;
}

const Weight: React.StatelessComponent<WeightProps> = ({ weight }) =>
  i18n.t("{{ value }} {{ unit }}", {
    context: "weight",
    ...weight
  });
Weight.displayName = "Weight";
export default Weight;
