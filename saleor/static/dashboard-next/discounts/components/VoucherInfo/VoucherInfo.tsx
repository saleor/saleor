import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import React from "react";

import Button from "@material-ui/core/Button";
import CardTitle from "@saleor/components/CardTitle";
import i18n from "../../../i18n";
import { FormErrors } from "../../../types";
import { FormData } from "../VoucherDetailsPage";

interface VoucherInfoProps {
  data: FormData;
  errors: FormErrors<"name" | "code" | "type">;
  disabled: boolean;
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
      gridTemplateColumns: "1fr"
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
    onChange
  }: VoucherInfoProps & WithStyles<typeof styles>) => {
    const [generateCode, setGenerateCode] = React.useState();
    const onGenerateCode = () => {
      let result = "";
      const characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
      for (let i = 0; i < 10; i++) {
        result += characters.charAt(
          Math.floor(Math.random() * characters.length)
        );
      }
      setGenerateCode(result);
    };

    const onChangeInput = event => {
      setGenerateCode(event.target.value);
      onChange(event);
    };
    return (
      <Card>
        <CardTitle
          title={i18n.t("General Information")}
          toolbar={
            <Button color="primary" onClick={onGenerateCode}>
              {i18n.t("Generate Code")}
            </Button>
          }
        />
        <CardContent>
          <div className={classes.root}>
            <TextField
              disabled={disabled}
              error={!!errors.code}
              fullWidth
              helperText={errors.code}
              name={"code" as keyof FormData}
              label={i18n.t("Discount Code")}
              value={generateCode || data.code}
              onChange={e => onChangeInput(e)}
            />
          </div>
        </CardContent>
      </Card>
    );
  }
);
export default VoucherInfo;
