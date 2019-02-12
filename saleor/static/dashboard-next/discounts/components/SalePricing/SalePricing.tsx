import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import {
  createStyles,
  Theme,
  WithStyles,
  withStyles
} from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import Hr from "../../../components/Hr";
import TextFieldWithChoice from "../../../components/TextFieldWithChoice";
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
      <Hr />
      <CardContent className={classes.root}>
        <Typography className={classes.subheading} variant="subheading">
          {i18n.t("Time Frame")}
        </Typography>
        <TextField
          disabled={disabled}
          error={!!errors.startDate}
          helperText={errors.startDate}
          name={"startDate" as keyof FormData}
          onChange={onChange}
          label={i18n.t("Start Date")}
          value={data.startDate}
          type="date"
          fullWidth
        />
        <TextField
          disabled={disabled}
          error={!!errors.endDate}
          helperText={errors.endDate}
          name={"endDate" as keyof FormData}
          onChange={onChange}
          label={i18n.t("End Date")}
          value={data.endDate}
          type="date"
          fullWidth
        />
      </CardContent>
    </Card>
  )
);
SalePricing.displayName = "SalePricing";
export default SalePricing;
