import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

interface HomeOrdersCardProps {
  userName: string;
}

const decorate = withStyles(theme => ({
  headerContainer: {
    marginBottom: theme.spacing.unit * 3,
    marginTop: theme.spacing.unit * 3
  },
  pageHeader: {
    fontWeight: 600 as 600
  }
}));

const HomeOrdersCard = decorate<HomeOrdersCardProps>(
  ({ classes, userName }) => {
    return (
      <div className={classes.headerContainer}>
        <Typography className={classes.pageHeader} variant={"headline"}>
          {userName ? (
            i18n.t("Hello there, {{userName}}", { userName })
          ) : (
            <Skeleton style={{ width: "10em" }} />
          )}
        </Typography>
        <Typography>
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
export default HomeOrdersCard;
