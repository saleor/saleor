import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import { FormSpacer } from "../../../components/FormSpacer";
import i18n from "../../../i18n";

interface VoucherDateProps {
  disabled?: boolean;
  data: {
    startDate: string;
    endDate: string | null;
    usageLimit: number | null;
  };
  onChange?(event: React.ChangeEvent<any>);
}

const decorate = withStyles(theme => ({ root: {} }));
const VoucherDate = decorate<VoucherDateProps>(
  ({ classes, data, disabled, onChange }) => (
    <Card>
      <CardContent>
        <TextField
          InputLabelProps={{ shrink: true }}
          disabled={disabled}
          fullWidth
          label={i18n.t("Active since")}
          name="startDate"
          onChange={onChange}
          type="date"
          value={data.startDate}
        />
        <FormSpacer />
        <TextField
          InputLabelProps={{ shrink: true }}
          disabled={disabled}
          fullWidth
          label={i18n.t("Active until")}
          name="endDate"
          onChange={onChange}
          type="date"
          value={data.endDate}
        />
        <FormSpacer />
        <TextField
          disabled={disabled}
          fullWidth
          label={i18n.t("Usage limit")}
          name="usageLimit"
          onChange={onChange}
          value={data.usageLimit}
        />
      </CardContent>
    </Card>
  )
);
VoucherDate.displayName = "VoucherDate";
export default VoucherDate;
