import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import CardTitle from "@saleor/components/CardTitle";
import ControlledSwitch from "@saleor/components/ControlledSwitch";
import { FormSpacer } from "@saleor/components/FormSpacer";
import Hr from "@saleor/components/Hr";
import RadioGroupField from "@saleor/components/RadioGroupField";
import TextFieldWithChoice from "@saleor/components/TextFieldWithChoice";
import i18n from "../../../i18n";
import { FormErrors } from "../../../types";
import { VoucherDiscountValueType } from "../../../types/globalTypes";
import { translateVoucherTypes } from "../../translations";
import { FormData } from "../VoucherDetailsPage";

interface VoucherValueProps {
  data: FormData;
  defaultCurrency: string;
  errors: FormErrors<"name" | "code" | "type">;
  disabled: boolean;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const enum VoucherTypeEnum {
  ENTIRE_ORDER = "ENTIRE_ORDER",
  SHIPPING = "SHIPPING",
  SPECIFIC_PRODUCT = "SPECIFIC_PRODUCT"
}

const styles = (theme: Theme) =>
  createStyles({
    root: {
      display: "grid",
      gridColumnGap: theme.spacing.unit * 2 + "px",
      gridTemplateColumns: "1fr"
    }
  });

const VoucherValue = withStyles(styles, {
  name: "VoucherValue"
})(
  ({
    classes,
    data,
    defaultCurrency,
    disabled,
    errors,
    onChange
  }: VoucherValueProps & WithStyles<typeof styles>) => {
    const translatedVoucherTypes = translateVoucherTypes();
    const voucherTypeChoices = Object.values(VoucherTypeEnum).map(type => ({
      hidden: type === "SHIPPING" ? true : false,
      label: translatedVoucherTypes[type],
      value: type
    }));

    return (
      <Card>
        <CardTitle title={i18n.t("Value")} />
        <CardContent>
          <div className={classes.root}>
            <TextFieldWithChoice
              disabled={disabled}
              error={!!errors.discountValue}
              ChoiceProps={{
                label:
                  data.discountType === VoucherDiscountValueType.FIXED
                    ? defaultCurrency
                    : "%",
                name: "discountType" as keyof FormData
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
            <FormSpacer />
            <RadioGroupField
              choices={voucherTypeChoices}
              disabled={disabled}
              error={!!errors.type}
              hint={errors.type}
              label="Discount Specific Information"
              name={"type" as keyof FormData}
              value={data.type}
              onChange={onChange}
            />
            <FormSpacer />
            <Hr />
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
          </div>
        </CardContent>
      </Card>
    );
  }
);
export default VoucherValue;
