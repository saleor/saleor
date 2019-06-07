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

import CardTitle from "@components/CardTitle";
import ControlledSwitch from "@components/ControlledSwitch";
import { FormSpacer } from "@components/FormSpacer";
import useDateLocalize from "../../hooks/useDateLocalize";
import i18n from "../../i18n";
import { DateContext } from "../Date/DateContext";

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
  children?: React.ReactNode | React.ReactNodeArray;
  data: {
    isPublished: boolean;
    publicationDate: string;
  };
  errors: { [key: string]: string };
  disabled?: boolean;
  onChange(event: any);
}

export const VisibilityCard = withStyles(styles, {
  name: "VisibilityCard"
})(
  ({
    children,
    classes,
    data: { isPublished, publicationDate },
    errors,
    disabled,
    onChange
  }: VisibilityCardProps) => {
    const localizeDate = useDateLocalize();
    const dateNow = React.useContext(DateContext);
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
                    ? i18n.t("since {{ date }}", {
                        date: localizeDate(publicationDate)
                      })
                    : Date.parse(publicationDate) > dateNow
                    ? i18n.t("will be visible from {{ date }}", {
                        date: localizeDate(publicationDate)
                      })
                    : null
                  : null
              }
              checked={isPublished}
              onChange={onChange}
              disabled={disabled}
            />
          </div>
          {!isPublished && (
            <>
              <TextField
                error={!!errors.publicationDate}
                disabled={disabled}
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
