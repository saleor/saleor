import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
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

const VoucherRequirements = withStyles(styles, {
  name: "VoucherRequirements"
})(
  ({
    classes,
    data,
    disabled,
    errors,
    onChange
  }: VoucherRequirementsProps & WithStyles<typeof styles>) => {
    return (
      <Card>
        <CardTitle title={i18n.t("Minimum Requirements")} />
        <CardContent>
          <div className={classes.root}>
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
          </div>
        </CardContent>
      </Card>
    );
  }
);
export default VoucherRequirements;
