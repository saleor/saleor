import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as moment from "moment-timezone";
import * as React from "react";

import CardTitle from "@saleor/components/CardTitle";
import { ControlledCheckbox } from "@saleor/components/ControlledCheckbox";
import i18n from "../../../i18n";
import { FormErrors } from "../../../types";
import { FormData } from "../VoucherDetailsPage";

interface VoucherDatesProps {
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

const VoucherDates = withStyles(styles, {
  name: "VoucherDates"
})(
  ({
    classes,
    data,
    disabled,
    errors,
    onChange
  }: VoucherDatesProps & WithStyles<typeof styles>) => {
    const [showEndDate, setshowEndDate] = React.useState(false);
    const handleOnChange = () => setshowEndDate(!showEndDate);

    console.log(data);

    return (
      <Card>
        <CardTitle title={i18n.t("Active Dates")} />
        <CardContent>
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
              error={!!errors.startDate}
              helperText={errors.startDate}
              name={"startTime" as keyof FormData}
              onChange={onChange}
              label={i18n.t("Start Hour")}
              value={data.startTime}
              type="time"
              fullWidth
            />
          </div>
          <ControlledCheckbox
            checked={showEndDate}
            label={i18n.t("Set end date")}
            name="setEndDate"
            onChange={handleOnChange}
          />
          {showEndDate ? (
            <div className={classes.root}>
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
              <TextField
                disabled={disabled}
                error={!!errors.endDate}
                helperText={errors.endDate}
                name={"endTime" as keyof FormData}
                onChange={onChange}
                label={i18n.t("End Hour")}
                value={data.endTime}
                type="time"
                fullWidth
              />
            </div>
          ) : null}
        </CardContent>
      </Card>
    );
  }
);
export default VoucherDates;
