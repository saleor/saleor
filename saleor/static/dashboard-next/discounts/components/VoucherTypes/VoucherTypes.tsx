import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import * as React from "react";

import CardTitle from "@saleor/components/CardTitle";
import Grid from "@saleor/components/Grid";
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

const VoucherTypes = ({
  data,
  disabled,
  errors,
  onChange
}: VoucherTypesProps) => {
  const voucherTypeChoices = [
    {
      label: i18n.t("Fixed Amount"),
      value: DiscountValueTypeEnum.FIXED
    },
    {
      label: i18n.t("Percentage"),
      value: DiscountValueTypeEnum.PERCENTAGE
    },
    {
      label: i18n.t("Free Shipping"),
      value: "SHIPPING"
    }
  ];

  return (
    <Card>
      <CardTitle title={i18n.t("Discount Type")} />
      <CardContent>
        <Grid variant="uniform">
          <RadioGroupField
            choices={voucherTypeChoices}
            disabled={disabled}
            error={!!errors.discountType}
            hint={errors.discountType}
            name={"discountType" as keyof FormData}
            value={data.discountType}
            onChange={onChange}
          />
        </Grid>
      </CardContent>
    </Card>
  );
};
export default VoucherTypes;
