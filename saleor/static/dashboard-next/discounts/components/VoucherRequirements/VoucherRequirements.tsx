import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import CardTitle from "@saleor/components/CardTitle";
import { FormSpacer } from "@saleor/components/FormSpacer";
import RadioGroupField from "@saleor/components/RadioGroupField";
import i18n from "@saleor/i18n";
import { FormErrors } from "@saleor/types";
import { RequirementsPickerEnum } from "../../../types/globalTypes";
import { FormData } from "../VoucherDetailsPage";

interface VoucherRequirementsProps {
  data: FormData;
  defaultCurrency: string;
  disabled: boolean;
  errors: FormErrors<"minAmountSpent" | "minCheckoutItemsQuantity">;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const VoucherRequirements = ({
  data,
  disabled,
  errors,
  onChange
}: VoucherRequirementsProps) => {
  const requirementsPickerChoices = [
    {
      label: i18n.t("None"),
      value: RequirementsPickerEnum.NONE
    },
    {
      label: i18n.t("Minimal order value"),
      value: RequirementsPickerEnum.ORDER
    },
    {
      label: i18n.t("Minimum quantity of items"),
      value: RequirementsPickerEnum.ITEM
    }
  ];

  return (
    <Card>
      <CardTitle title={i18n.t("Minimum Requirements")} />
      <CardContent>
        <RadioGroupField
          choices={requirementsPickerChoices}
          disabled={disabled}
          name={"requirementsPicker" as keyof FormData}
          value={data.requirementsPicker}
          onChange={onChange}
        />
        <FormSpacer />
        {data.requirementsPicker === RequirementsPickerEnum.ORDER ? (
          <TextField
            disabled={disabled}
            error={!!errors.minAmountSpent}
            helperText={errors.minAmountSpent}
            label={i18n.t("Minimal order value")}
            name={"minAmountSpent" as keyof FormData}
            value={data.minAmountSpent}
            onChange={onChange}
            fullWidth
          />
        ) : data.requirementsPicker === RequirementsPickerEnum.ITEM ? (
          <TextField
            disabled={disabled}
            error={!!errors.minCheckoutItemsQuantity}
            helperText={errors.minCheckoutItemsQuantity}
            label={i18n.t("Minimum quantity of items")}
            name={"minCheckoutItemsQuantity" as keyof FormData}
            value={data.minCheckoutItemsQuantity}
            onChange={onChange}
            fullWidth
          />
        ) : null}
      </CardContent>
    </Card>
  );
};
export default VoucherRequirements;
