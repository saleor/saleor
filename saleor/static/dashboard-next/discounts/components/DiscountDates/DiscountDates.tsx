import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import CardTitle from "@saleor/components/CardTitle";
import { ControlledCheckbox } from "@saleor/components/ControlledCheckbox";
import Grid from "@saleor/components/Grid";
import { ChangeEvent } from "@saleor/hooks/useForm";
import i18n from "@saleor/i18n";
import { FormErrors } from "@saleor/types";

export interface DiscountDatesFormData {
  endDate: string;
  endTime: string;
  hasEndDate: boolean;
  startDate: string;
  startTime: string;
}

interface DiscountDatesProps {
  data: DiscountDatesFormData;
  defaultCurrency: string;
  disabled: boolean;
  errors: FormErrors<"endDate" | "startDate">;
  onChange: (event: ChangeEvent<DiscountDatesFormData>) => void;
}

const DiscountDates: React.FC<DiscountDatesProps> = ({
  data,
  disabled,
  errors,
  onChange
}) => (
  <Card>
    <CardTitle title={i18n.t("Active Dates")} />
    <CardContent>
      <Grid variant="uniform">
        <TextField
          disabled={disabled}
          error={!!errors.startDate}
          helperText={errors.startDate}
          name={"startDate" as keyof DiscountDatesFormData}
          onChange={onChange}
          label={i18n.t("Start Date")}
          value={data.startDate}
          type="date"
          fullWidth
          InputLabelProps={{
            shrink: true
          }}
        />
        <TextField
          disabled={disabled}
          error={!!errors.startDate}
          helperText={errors.startDate}
          name={"startTime" as keyof DiscountDatesFormData}
          onChange={onChange}
          label={i18n.t("Start Hour")}
          value={data.startTime}
          type="time"
          fullWidth
          InputLabelProps={{
            shrink: true
          }}
        />
      </Grid>
      <ControlledCheckbox
        checked={data.hasEndDate}
        label={i18n.t("Set end date")}
        name={"hasEndDate" as keyof DiscountDatesFormData}
        onChange={onChange}
      />
      {data.hasEndDate && (
        <Grid variant="uniform">
          <TextField
            disabled={disabled}
            error={!!errors.endDate}
            helperText={errors.endDate}
            name={"endDate" as keyof DiscountDatesFormData}
            onChange={onChange}
            label={i18n.t("End Date")}
            value={data.endDate}
            type="date"
            fullWidth
            InputLabelProps={{
              shrink: true
            }}
          />
          <TextField
            disabled={disabled}
            error={!!errors.endDate}
            helperText={errors.endDate}
            name={"endTime" as keyof DiscountDatesFormData}
            onChange={onChange}
            label={i18n.t("End Hour")}
            value={data.endTime}
            type="time"
            fullWidth
            InputLabelProps={{
              shrink: true
            }}
          />
        </Grid>
      )}
    </CardContent>
  </Card>
);
export default DiscountDates;
