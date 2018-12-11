import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { StaffMemberDetails_user } from "../../types/StaffMemberDetails";

const styles = (theme: Theme) =>
  createStyles({
    avatar: {
      alignItems: "center",
      backgroundColor: theme.palette.primary.main,
      borderRadius: "100%",
      display: "grid",
      height: 120,
      justifyContent: "center",
      width: 120
    },
    avatarText: {
      color: "#ffffff",
      fontSize: 64,
      pointerEvents: "none"
    },
    prop: {
      marginBottom: theme.spacing.unit * 0
    },
    propGrid: {
      display: "grid",
      gridColumnGap: theme.spacing.unit * 2 + "px",
      gridTemplateColumns: "1fr 1fr"
    },
    root: {
      display: "grid",
      gridColumnGap: theme.spacing.unit * 4 + "px",
      gridTemplateColumns: "120px 1fr"
    }
  });

interface StaffPropertiesProps extends WithStyles<typeof styles> {
  className?: string;
  staffMember: StaffMemberDetails_user;
}

const StaffProperties = withStyles(styles, { name: "StaffProperties" })(
  ({ classes, className, staffMember }: StaffPropertiesProps) => (
    <Card className={className}>
      <CardTitle title={i18n.t("Staff Member Information")} />
      <CardContent>
        <div className={classes.root}>
          <div>
            <div className={classes.avatar}>
              <Typography className={classes.avatarText}>
                {maybe(() => staffMember.email.slice(0, 2).toUpperCase()) || ""}
              </Typography>
            </div>
          </div>
          <div>
            <div className={classes.propGrid}>
              <div>
                <div className={classes.prop}>
                  <Typography variant="body2">{i18n.t("E-mail")}</Typography>
                  {maybe(() => staffMember.email) === undefined ? (
                    <Skeleton />
                  ) : (
                    <Typography>{staffMember.email}</Typography>
                  )}
                </div>
                <div />
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
