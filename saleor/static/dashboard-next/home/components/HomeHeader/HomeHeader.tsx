import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

const styles = (theme: Theme) =>
  createStyles({
    headerContainer: {
      marginBottom: theme.spacing.unit * 3
    },
    pageHeader: {
      fontWeight: 600 as 600
    },
    subtitle: {
      color: theme.typography.caption.color
    }
  });

interface HomeOrdersCardProps extends WithStyles<typeof styles> {
  userName: string;
}

const HomeOrdersCard = withStyles(styles, { name: "HomeOrdersCard" })(
  ({ classes, userName }: HomeOrdersCardProps) => {
    return (
      <div className={classes.headerContainer}>
        <Typography className={classes.pageHeader} variant="display1">
          {userName ? (
            i18n.t("Hello there, {{userName}}", { userName })
          ) : (
            <Skeleton style={{ width: "10em" }} />
          )}
        </Typography>
        <Typography className={classes.subtitle}>
          {userName ? (
            i18n.t("Here are some information we gathered about your store")
          ) : (
            <Skeleton style={{ width: "10em" }} />
          )}
        </Typography>
      </div>
    );
  }
);
HomeOrdersCard.displayName = "HomeOrdersCard";
export default HomeOrdersCard;
