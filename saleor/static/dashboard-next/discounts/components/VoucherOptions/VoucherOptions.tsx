import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import ControlledSwitch from "../../../components/ControlledSwitch";
import FormSpacer from "../../../components/FormSpacer";
import Hr from "../../../components/Hr";
import TextFieldWithChoice from "../../../components/TextFieldWithChoice";
import i18n from "../../../i18n";
import { FormErrors } from "../../../types";
import { VoucherDiscountValueType } from "../../../types/globalTypes";
import { FormData } from "../VoucherDetailsPage";

interface VoucherOptionsProps {
  data: FormData;
  defaultCurrency: string;
  disabled: boolean;
  errors: FormErrors<
    | "discountType"
    | "discountValue"
    | "endDate"
    | "minAmountSpent"
    | "startDate"
    | "usageLimit"
  >;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    root: {
      display: "grid",
      gridColumnGap: theme.spacing.unit * 2 + "px",
      gridTemplateColumns: "1fr 1fr"
    }
  });

const VoucherOptions = withStyles(styles, {
  name: "VoucherOptions"
})(
  ({
    classes,
    data,
    defaultCurrency,
    disabled,
    errors,
    onChange
  }: VoucherOptionsProps & WithStyles<typeof styles>) => (
    <Card>
      <CardTitle title={i18n.t("Detailed Informations")} />
      <CardContent className={classes.root}>
        <TextFieldWithChoice
          disabled={disabled}
          error={!!errors.discountValue}
          ChoiceProps={{
            label:
              data.discountType === VoucherDiscountValueType.FIXED
                ? defaultCurrency
                : "%",
            name: "discountType" as keyof FormData,
            values: [
              {
                label: defaultCurrency,
                value: VoucherDiscountValueType.FIXED
              },
              {
                label: "%",
                value: VoucherDiscountValueType.PERCENTAGE
              }
            ]
          }}
          helperText={errors.discountValue}
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
        <TextField
          disabled={disabled}
          error={!!errors.usageLimit}
          helperText={errors.usageLimit || i18n.t("Optional")}
          name={"usageLimit" as keyof FormData}
          value={data.usageLimit}
          onChange={onChange}
          label={i18n.t("Usage Limit")}
          type="number"
          inputProps={{
            min: 0
          }}
          fullWidth
        />
      </CardContent>
      <Hr />
      <CardContent>
        <Typography variant="subheading">
          {i18n.t("Discount Specific Information")}
        </Typography>
        <FormSpacer />
        <div className={classes.root}>
          <TextField
            disabled={disabled}
            error={!!errors.minAmountSpent}
            helperText={errors.minAmountSpent || i18n.t("Optional")}
            name={"minAmountSpent" as keyof FormData}
            value={data.minAmountSpent}
            onChange={onChange}
            label={i18n.t("Minimum order value")}
            fullWidth
          />
        </div>
        <FormSpacer />
        <ControlledSwitch
          checked={data.applyOncePerOrder}
          label={
            <>
              {i18n.t("Only once per order", {
                context: "voucher application"
              })}
              <Typography variant="caption">
                {i18n.t(
                  "If this option is disabled, discount will be counted for every eligible product"
                )}
              </Typography>
            </>
          }
          onChange={onChange}
          name={"applyOncePerOrder" as keyof FormData}
          disabled={disabled}
        />
      </CardContent>
      <Hr />
      <CardContent>
        <Typography variant="subheading">{i18n.t("Time Frame")}</Typography>
        <FormSpacer />
        <div className={classes.root}>
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
        </div>
      </CardContent>
    </Card>
  )
);
export default VoucherOptions;
