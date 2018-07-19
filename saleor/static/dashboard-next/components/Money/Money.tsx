import Typography, { TypographyProps } from "@material-ui/core/Typography";
import * as React from "react";

interface MoneyProps {
  amount: number;
  currency: string;
  typographyProps?: TypographyProps;
}

export const Money: React.StatelessComponent<MoneyProps> = ({
  amount,
  currency,
  typographyProps
}) => {
  const money =
    currency === "%"
      ? [amount, currency].join(" ")
      : amount.toLocaleString(navigator.language, {
          currency,
          style: "currency"
        });
  if (typographyProps) {
    return <Typography {...typographyProps}>{money}</Typography>;
  }
  return <>{money}</>;
};
export default Money;
