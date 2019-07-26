import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import {
  createStyles,
  Theme,
  WithStyles,
  withStyles
} from "@material-ui/core/styles";
import React from "react";

import CardTitle from "@saleor/components/CardTitle";
import TextFieldWithChoice from "@saleor/components/TextFieldWithChoice";
import i18n from "../../../i18n";
import { FormErrors } from "../../../types";
import { SaleType } from "../../../types/globalTypes";
import { FormData } from "../SaleDetailsPage";

export interface SalePricingProps {
  data: FormData;
  defaultCurrency: string;
  disabled: boolean;
  errors: FormErrors<"startDate" | "endDate" | "value">;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    root: {
      display: "grid",
      gridColumnGap: theme.spacing.unit * 2 + "px",
      gridTemplateColumns: "1fr 1fr"
    },
    subheading: {
      gridColumnEnd: "span 2",
      marginBottom: theme.spacing.unit * 2
    }
  });

const SalePricing = withStyles(styles, {
  name: "SalePricing"
})(
  ({
    classes,
    data,
    defaultCurrency,
    disabled,
    errors,
    onChange
  }: SalePricingProps & WithStyles<typeof styles>) => (
    <Card>
      <CardTitle title={i18n.t("Pricing")} />
      <CardContent className={classes.root}>
        <TextFieldWithChoice
          disabled={disabled}
          ChoiceProps={{
            label: data.type === SaleType.FIXED ? defaultCurrency : "%",
            name: "type",
            values: [
              {
                label: defaultCurrency,
                value: SaleType.FIXED
              },
              {
                label: "%",
                value: SaleType.PERCENTAGE
              }
            ]
          }}
          error={!!errors.value}
          helperText={errors.value}
          name={"value" as keyof FormData}
          onChange={onChange}
          label={i18n.t("Discount Value")}
          value={data.value}
          type="number"
          fullWidth
          inputProps={{
            min: 0
          }}
        />
      </CardContent>
    </Card>
  )
);
SalePricing.displayName = "SalePricing";
export default SalePricing;
