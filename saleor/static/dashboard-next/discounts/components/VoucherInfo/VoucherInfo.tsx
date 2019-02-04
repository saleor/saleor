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
import FormSpacer from "../../../components/FormSpacer";
import SingleSelectField from "../../../components/SingleSelectField";
import i18n from "../../../i18n";
import { FormErrors } from "../../../types";
import { VoucherType } from "../../../types/globalTypes";
import { translateVoucherTypes } from "../../translations";
import { FormData } from "../VoucherDetailsPage";

interface VoucherInfoProps {
  data: FormData;
  errors: FormErrors<"name" | "code" | "type">;
  disabled: boolean;
  variant: "create" | "update";
  onChange: (event: React.ChangeEvent<any>) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    nameInput: {
      gridColumnEnd: "span 2"
    },
    root: {
      display: "grid",
      gridColumnGap: theme.spacing.unit * 2 + "px",
      gridTemplateColumns: "1fr 1fr"
    }
  });

const VoucherInfo = withStyles(styles, {
  name: "VoucherInfo"
})(
  ({
    classes,
    data,
    disabled,
    errors,
    variant,
    onChange
  }: VoucherInfoProps & WithStyles<typeof styles>) => {
    const translatedVoucherTypes = translateVoucherTypes();
    const voucherTypeChoices = Object.values(VoucherType).map(type => ({
      label: translatedVoucherTypes[type],
      value: type
    }));

    return (
      <Card>
        <CardTitle title={i18n.t("General Informations")} />
        <CardContent>
          <TextField
            className={classes.nameInput}
            disabled={disabled}
            error={!!errors.name}
            fullWidth
            helperText={errors.name}
            name={"name" as keyof FormData}
            label={i18n.t("Name")}
            value={data.name}
            onChange={onChange}
          />
          <FormSpacer />
          <div className={classes.root}>
            <TextField
              disabled={disabled}
              error={!!errors.code}
              fullWidth
              helperText={errors.code}
              name={"code" as keyof FormData}
              label={i18n.t("Discount Code")}
              value={data.code}
              onChange={onChange}
            />
            <SingleSelectField
              choices={voucherTypeChoices}
              disabled={disabled || variant === "update"}
              error={!!errors.type}
              hint={errors.type}
              name={"type" as keyof FormData}
              label={i18n.t("Type of Discount")}
              value={data.type}
              onChange={onChange}
            />
          </div>
        </CardContent>
      </Card>
    );
  }
);
export default VoucherInfo;
