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
import { ControlledCheckbox } from "@saleor/components/ControlledCheckbox";
import i18n from "../../../i18n";
import { FormErrors } from "../../../types";
import { FormData } from "../VoucherDetailsPage";

interface VoucherLimitsProps {
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
      gridTemplateColumns: "1fr"
    }
  });

const VoucherLimits = withStyles(styles, {
  name: "VoucherLimits"
})(
  ({
    classes,
    data,
    disabled,
    errors,
    onChange
  }: VoucherLimitsProps & WithStyles<typeof styles>) => {
    const [showInput, setshowInput] = React.useState(false);
    const handleOnChange = () => setshowInput(!showInput);
    return (
      <Card>
        <CardTitle title={i18n.t("Usage Limit ")} />
        <CardContent className={classes.root}>
          <ControlledCheckbox
            checked={showInput}
            label={i18n.t(
              "Limit number of times this discount can be used in total"
            )}
            name="usageLimitCheck"
            onChange={handleOnChange}
          />
          {showInput ? (
            <TextField
              disabled={disabled}
              error={!!errors.usageLimit}
              helperText={errors.usageLimit}
              label={i18n.t("Limit of Uses")}
              name={"usageLimit" as keyof FormData}
              value={data.usageLimit}
              onChange={onChange}
              type="number"
              inputProps={{
                min: 0
              }}
              fullWidth
            />
          ) : null}
        </CardContent>
      </Card>
    );
  }
);
export default VoucherLimits;
