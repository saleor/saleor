import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { IconProps } from "@material-ui/core/Icon";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

interface HomeAnalyticsCardProps {
  icon: React.ReactElement<IconProps>;
  title: string;
  children?: React.ReactNode;
}

const decorate = withStyles(theme => ({
  cardContent: {
    "&:last-child": {
      paddingBottom: 16
    },
    display: "grid" as "grid",
    gridColumnGap: theme.spacing.unit * 1 + "px",
    gridTemplateColumns: "1fr 64px"
  },
  cardSpacing: {
    [theme.breakpoints.down("sm")]: {
      marginBottom: theme.spacing.unit
    },
    marginBottom: theme.spacing.unit * 3
  },
  cardSubtitle: {
    color: theme.palette.text.secondary,
    height: "20px",
    lineHeight: 0.9
  },
  cardTitle: {
    fontWeight: 600 as 600
  },
  icon: {
    color: theme.palette.primary.contrastText,
    fontSize: 54,
    margin: ".5rem .3rem"
  },
  iconBackground: {
    backgroundColor: theme.palette.primary.main,
    borderRadius: "8px",
    color: "white",
    fontSize: "54px",
    height: "100%",
    padding: "10px 5px 0px 5px",
    width: "100%"
  }
}));
const HomeAnalyticsCard = decorate<HomeAnalyticsCardProps>(
  ({ children, classes, title, icon }) => (
    <Card className={classes.cardSpacing}>
      <CardContent className={classes.cardContent}>
        <div>
          <Typography className={classes.cardTitle} variant="subheading">
            {title}
          </Typography>
          <Typography
            className={classes.cardSubtitle}
            variant="caption"
            color="textSecondary"
          >
            {i18n.t("Today")}
          </Typography>
          <Typography color={"textPrimary"} variant="headline">
            {children ? children : <Skeleton style={{ width: "5em" }} />}
          </Typography>
        </div>
        <div className={classes.iconBackground}>{icon}</div>
      </CardContent>
    </Card>
  )
);
export default HomeAnalyticsCard;
