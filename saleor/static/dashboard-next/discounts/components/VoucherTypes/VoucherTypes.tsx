import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import * as React from "react";

import CardTitle from "@saleor/components/CardTitle";
import RadioGroupField from "@saleor/components/RadioGroupField";
import i18n from "../../../i18n";
import { FormErrors } from "../../../types";
import { VoucherType } from "../../../types/globalTypes";
import { translateVoucherTypes } from "../../translations";
import { FormData } from "../VoucherDetailsPage";

interface VoucherTypesProps {
  data: FormData;
  errors: FormErrors<"name" | "code" | "type">;
  disabled: boolean;
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

const VoucherTypes = withStyles(styles, {
  name: "VoucherTypes"
})(
  ({
    classes,
    data,
    disabled,
    errors,
    onChange
  }: VoucherTypesProps & WithStyles<typeof styles>) => {
    const translatedVoucherTypes = translateVoucherTypes();
    const voucherTypeChoices = Object.values(VoucherType).map(type => ({
      label: translatedVoucherTypes[type],
      value: type
    }));

    return (
      <Card>
        <CardTitle title={i18n.t("Discount Type")} />
        <CardContent>
          <div className={classes.root}>
            <RadioGroupField
              choices={voucherTypeChoices}
              disabled={disabled}
              error={!!errors.type}
              hint={errors.type}
              name={"type" as keyof FormData}
              value={data.type}
              onChange={onChange}
            />
          </div>
        </CardContent>
      </Card>
    );
  }
);
export default VoucherTypes;
