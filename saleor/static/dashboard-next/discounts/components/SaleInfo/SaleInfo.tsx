import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import {
  createStyles,
  Theme,
  WithStyles,
  withStyles
} from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import i18n from "../../../i18n";
import { FormData } from "../SaleDetailsPage";

export interface SaleInfoProps {
  data: FormData;
  disabled: boolean;
  errors: {
    name?: string;
  };
  onChange: (event: React.ChangeEvent<any>) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    root: {
      display: "grid",
      gridColumnGap: theme.spacing.unit * 2 + "px",
      gridTemplateColumns: "3fr 1fr"
    }
  });

const SaleInfo = withStyles(styles, {
  name: "SaleInfo"
})(
  ({
    classes,
    data,
    disabled,
    errors,
    onChange
  }: SaleInfoProps & WithStyles<typeof styles>) => (
    <Card>
      <CardTitle title={i18n.t("General Informations")} />
      <CardContent className={classes.root}>
        <TextField
          disabled={disabled}
          error={!!errors.name}
          helperText={errors.name}
          name={"name" as keyof FormData}
          onChange={onChange}
          label={i18n.t("Name")}
          value={data.name}
          fullWidth
        />
      </CardContent>
    </Card>
  )
);
SaleInfo.displayName = "SaleInfo";
export default SaleInfo;
