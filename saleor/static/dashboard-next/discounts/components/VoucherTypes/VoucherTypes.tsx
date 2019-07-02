import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import * as React from "react";

import CardTitle from "@saleor/components/CardTitle";
import RadioGroupField from "@saleor/components/RadioGroupField";
import i18n from "../../../i18n";
import { FormErrors } from "../../../types";
import { DiscountValueTypeEnum } from "../../../types/globalTypes";
import { FormData } from "../VoucherDetailsPage";

interface VoucherTypesProps {
  data: FormData;
  errors: FormErrors<"discountType">;
  disabled: boolean;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    root: {
      display: "grid",
      gridColumnGap: theme.spacing.unit * 2 + "px",
      gridTemplateColumns: "1fr"
    }
  });

const VoucherTypes = withStyles(styles, {
  name: "VoucherTypes"
})(
  ({
    classes,
    data,
    disabled,
    errors,
    onChange
  }: VoucherTypesProps & WithStyles<typeof styles>) => {
    const voucherTypeChoices = Object.values(DiscountValueTypeEnum).map(
      type => {
        switch (type.toString()) {
          case DiscountValueTypeEnum.FIXED:
            return {
              hidden: false,
              label: i18n.t("Fixed Amount"),
              value: type
            };
          case DiscountValueTypeEnum.PERCENTAGE:
            return {
              hidden: false,
              label: i18n.t("Percentage"),
              value: type
            };
        }
      }
    );

    voucherTypeChoices.push({
      hidden: false,
      label: i18n.t("Free Shipping"),
      value: "SHIPPING"
    });

    return (
      <Card>
        <CardTitle title={i18n.t("Discount Type")} />
        <CardContent>
          <div className={classes.root}>
            <RadioGroupField
              choices={voucherTypeChoices}
              disabled={disabled}
              error={!!errors.discountType}
              hint={errors.discountType}
              name={"discountType" as keyof FormData}
              value={data.discountType}
              onChange={onChange}
            />
          </div>
        </CardContent>
      </Card>
    );
  }
);
export default VoucherTypes;
