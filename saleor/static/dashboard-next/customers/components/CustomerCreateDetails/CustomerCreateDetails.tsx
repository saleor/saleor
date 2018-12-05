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

import CardTitle from "../../../components/CardTitle";
import i18n from "../../../i18n";

const styles = (theme: Theme) =>
  createStyles({
    root: {
      display: "grid",
      gridColumnGap: theme.spacing.unit * 2 + "px",
      gridTemplateColumns: "1fr 1fr"
    }
  });

export interface CustomerCreateDetailsProps extends WithStyles<typeof styles> {
  data: {
    email: string;
  };
  disabled: boolean;
  errors: Partial<{
    email: string;
  }>;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const CustomerCreateDetails = withStyles(styles, {
  name: "CustomerCreateDetails"
})(
  ({
    classes,
    data,
    disabled,
    errors,
    onChange
  }: CustomerCreateDetailsProps) => (
    <Card>
      <CardTitle title={i18n.t("Customer overview")} />
      <CardContent>
        <div className={classes.root}>
          <TextField
            disabled={disabled}
            error={!!errors.email}
            fullWidth
            name="email"
            label={i18n.t("E-mail")}
            helperText={errors.email}
            type="email"
            value={data.email}
            onChange={onChange}
          />
        </div>
      </CardContent>
    </Card>
  )
);
CustomerCreateDetails.displayName = "CustomerCreateDetails";
export default CustomerCreateDetails;
