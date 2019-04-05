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
import { maybe } from "../../../misc";
import { StaffMemberDetails_user } from "../../types/StaffMemberDetails";

const styles = (theme: Theme) =>
  createStyles({
    avatar: {
      alignItems: "center",
      borderRadius: "100%",
      display: "grid",
      height: 120,
      justifyContent: "center",
      width: 120
    },
    avatarImage: {
      pointerEvents: "none",
      width: "100%"
    },
    prop: {
      marginBottom: theme.spacing.unit * 2 + "px"
    },
    propGrid: {
      display: "grid",
      gridColumnGap: theme.spacing.unit * 2 + "px",
      gridRowGap: theme.spacing.unit + "px",
      gridTemplateColumns: "1fr 1fr",
      [theme.breakpoints.down("xs")]: {
        gridTemplateColumns: "1fr"
      }
    },
    root: {
      display: "grid",
      gridColumnGap: theme.spacing.unit * 4 + "px",
      gridTemplateColumns: "120px 1fr"
    }
  });

interface StaffPropertiesProps extends WithStyles<typeof styles> {
  className?: string;
  data: {
    email: string;
    firstName: string;
    lastName: string;
  };
  disabled: boolean;
  staffMember: StaffMemberDetails_user;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const StaffProperties = withStyles(styles, { name: "StaffProperties" })(
  ({
    classes,
    className,
    data,
    staffMember,
    onChange
  }: StaffPropertiesProps) => (
    <Card className={className}>
      <CardTitle title={i18n.t("Staff Member Information")} />
      <CardContent>
        <div className={classes.root}>
          <div>
            <div className={classes.avatar}>
              <img
                className={classes.avatarImage}
                src={maybe(() => staffMember.avatar.url)}
              />
            </div>
          </div>
          <div>
            <div className={classes.propGrid}>
              <div className={classes.prop}>
                <TextField
                  label={i18n.t("First Name")}
                  value={data.firstName}
                  name="firstName"
                  onChange={onChange}
                  fullWidth
                />
              </div>
              <div className={classes.prop}>
                <TextField
                  label={i18n.t("Last Name")}
                  value={data.lastName}
                  name="lastName"
                  onChange={onChange}
                  fullWidth
                />
              </div>
              <div className={classes.prop}>
                <TextField
                  label={i18n.t("E-mail")}
                  value={data.email}
                  name="email"
                  onChange={onChange}
                  fullWidth
                />
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
);
StaffProperties.displayName = "StaffProperties";
export default StaffProperties;
