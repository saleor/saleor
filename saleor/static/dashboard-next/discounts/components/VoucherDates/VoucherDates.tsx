import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import CardTitle from "@saleor/components/CardTitle";
import { ControlledCheckbox } from "@saleor/components/ControlledCheckbox";
import Grid from "@saleor/components/Grid";
import i18n from "../../../i18n";
import { FormErrors } from "../../../types";
import { FormData } from "../VoucherDetailsPage";

interface VoucherDatesProps {
  data: FormData;
  defaultCurrency: string;
  disabled: boolean;
  errors: FormErrors<"endDate" | "startDate">;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const VoucherDates = ({
  data,
  disabled,
  errors,
  onChange
}: VoucherDatesProps) => {
  return (
    <Card>
      <CardTitle title={i18n.t("Active Dates")} />
      <CardContent>
        <Grid variant="uniform">
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
        </Grid>
        <ControlledCheckbox
          checked={data.hasEndDate}
          label={i18n.t("Set end date")}
          name={"hasEndDate" as keyof FormData}
          onChange={onChange}
        />
        {data.hasEndDate && (
          <Grid variant="uniform">
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
          </Grid>
        )}
      </CardContent>
    </Card>
  );
};
export default VoucherDates;
