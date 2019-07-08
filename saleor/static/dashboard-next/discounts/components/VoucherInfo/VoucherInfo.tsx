import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import TextField from "@material-ui/core/TextField";
import React from "react";

import Button from "@material-ui/core/Button";
import CardTitle from "@saleor/components/CardTitle";
import i18n from "../../../i18n";
import { generateCode } from "../../../misc";
import { FormErrors } from "../../../types";
import { FormData } from "../VoucherDetailsPage";

interface VoucherInfoProps {
  data: FormData;
  errors: FormErrors<"code">;
  disabled: boolean;
  variant: "create" | "update";
  onChange: (event: any) => void;
}

const VoucherInfo = ({
  data,
  disabled,
  errors,
  variant,
  onChange
}: VoucherInfoProps) => {
  const onGenerateCode = () =>
    onChange({
      target: {
        name: "code",
        value: generateCode(10)
      }
    });

  return (
    <Card>
      <CardTitle
        title={i18n.t("General Information")}
        toolbar={
          variant === "create" && (
            <Button color="primary" onClick={onGenerateCode}>
              {i18n.t("Generate Code")}
            </Button>
          )
        }
      />
      <CardContent>
        <TextField
          disabled={variant === "update" || disabled}
          error={!!errors.code}
          fullWidth
          helperText={errors.code}
          name={"code" as keyof FormData}
          label={i18n.t("Discount Code")}
          value={data.code}
          onChange={onChange}
        />
      </CardContent>
    </Card>
  );
};
export default VoucherInfo;
