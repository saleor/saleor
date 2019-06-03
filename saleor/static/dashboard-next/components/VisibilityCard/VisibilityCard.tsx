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

import CardTitle from "../../components/CardTitle";
import ControlledSwitch from "../../components/ControlledSwitch";
import { FormSpacer } from "../../components/FormSpacer";
import i18n from "../../i18n";

const styles = (theme: Theme) =>
  createStyles({
    date: {
      "& svg": {
        fill: theme.palette.primary.main
      },
      marginTop: theme.spacing.unit * 4
    },
    expandedSwitchContainer: {
      marginBottom: 0
    },
    switchContainer: {
      marginBottom: -theme.spacing.unit
    }
  });

interface VisibilityCardProps extends WithStyles<typeof styles> {
  children?: React.ReactNode;
  data: {
    isPublished: boolean;
    publicationDate: string;
  };
  errors: { [key: string]: string };
  loading?: boolean;
  onChange(event: any);
}

export const VisibilityCard = withStyles(styles, {
  name: "PVisibilityCard"
})(
  ({
    children,
    classes,
    data: { isPublished, publicationDate },
    errors,
    loading,
    onChange
  }: VisibilityCardProps) => {
    return (
      <Card>
        <CardTitle title={i18n.t("Visibility")} />
        <CardContent>
          <div
            className={
              isPublished
                ? classes.expandedSwitchContainer
                : classes.switchContainer
            }
          >
            <ControlledSwitch
              name="isPublished"
              label={i18n.t("Visible")}
              uncheckedLabel={i18n.t("Hidden")}
              secondLabel={
                publicationDate
                  ? isPublished
                    ? i18n.t("since ") + publicationDate
                    : Date.parse(publicationDate) > Date.now()
                    ? i18n.t("will be visible on ") + publicationDate
                    : null
                  : null
              }
              checked={isPublished}
              onChange={onChange}
              disabled={loading}
            />
          </div>
          {!isPublished && (
            <>
              <TextField
                error={!!errors.publicationDate}
                disabled={loading}
                label={i18n.t("Publish on")}
                name="publicationDate"
                type="date"
                fullWidth={true}
                helperText={errors.publicationDate}
                value={publicationDate ? publicationDate : ""}
                onChange={onChange}
                className={classes.date}
                InputLabelProps={{
                  shrink: true
                }}
              />
            </>
          )}
          <FormSpacer />
          {children}
        </CardContent>
      </Card>
    );
  }
);
VisibilityCard.displayName = "VisibilityCard";
export default VisibilityCard;
