import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import FormSpacer from "../../../components/FormSpacer";
import SingleSelectField from "../../../components/SingleSelectField";
import i18n from "../../../i18n";

interface VoucherDetailsProps {
  currency?: string;
  disabled?: boolean;
  voucher?: {
    id: string;
    name: string | null;
    code: string;
    usageLimit: number | null;
    used: number | null;
    startDate: string | null;
    endDate: string | null;
    discountValueType: "PERCENTAGE" | "FIXED" | string;
    discountValue: number;
    product: {
      id: string;
      name: string;
      price: { amount: number; currency: string };
    } | null;
    category: {
      id: string;
      name: string;
      products: { totalCount: number };
    } | null;
    applyTo: string | null;
    limit: { amount: number; currency: string } | null;
  };
  data: {
    code: string;
    discountValueType: string;
    discountValue: number;
    name: string;
  };
  onChange?(event: React.ChangeEvent<any>);
}

const decorate = withStyles(theme => ({
  grid: {
    display: "grid" as "grid",
    gridColumnGap: theme.spacing.unit * 2 + "px",
    gridTemplateColumns: "1fr 10rem"
  }
}));
const VoucherDetails = decorate<VoucherDetailsProps>(
  ({ classes, currency, data, disabled, onChange }) => (
    <Card>
      <CardContent>
        <TextField
          disabled={disabled}
          fullWidth
          label={i18n.t("Code")}
          name="code"
          onChange={onChange}
          value={data.code}
        />
        <FormSpacer />
        <TextField
          disabled={disabled}
          fullWidth
          helperText={i18n.t("Optional")}
          label={i18n.t("Name")}
          name="name"
          onChange={onChange}
          value={data.name}
        />
        <FormSpacer />
        <div className={classes.grid}>
          <div>
            <TextField
              disabled={disabled}
              fullWidth
              label={i18n.t("Discount value")}
              name="discountValue"
              onChange={onChange}
              type="number"
              value={data.discountValue}
            />
          </div>
          <div>
            <SingleSelectField
              choices={[
                { label: "%", value: "PERCENTAGE" },
                { label: currency, value: "FIXED" }
              ]}
              disabled={disabled}
              label={i18n.t("Discount type")}
              name="discountValueType"
              onChange={onChange}
              value={data.discountValueType}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  )
);
VoucherDetails.displayName = "VoucherDetails";
export default VoucherDetails;
