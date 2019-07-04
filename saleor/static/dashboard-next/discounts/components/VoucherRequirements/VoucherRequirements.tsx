import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import CardTitle from "@saleor/components/CardTitle";
import i18n from "../../../i18n";
import { FormErrors } from "../../../types";
import { FormData } from "../VoucherDetailsPage";

interface VoucherRequirementsProps {
  data: FormData;
  defaultCurrency: string;
  disabled: boolean;
  errors: FormErrors<"minAmountSpent">;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const VoucherRequirements = ({
  data,
  disabled,
  errors,
  onChange
}: VoucherRequirementsProps) => {
  return (
    <Card>
      <CardTitle title={i18n.t("Minimum Requirements")} />
      <CardContent>
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
      </CardContent>
    </Card>
  );
};
export default VoucherRequirements;
