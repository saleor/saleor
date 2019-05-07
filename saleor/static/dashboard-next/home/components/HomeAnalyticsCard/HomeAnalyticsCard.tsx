import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { IconProps } from "@material-ui/core/Icon";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import i18n from "../../../i18n";

const styles = (theme: Theme) =>
  createStyles({
    cardContent: {
      "&:last-child": {
        paddingBottom: 16
      },
      display: "grid",
      gridColumnGap: theme.spacing.unit * 3 + "px",
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
      backgroundColor: theme.palette.background.default,
      borderRadius: "8px",
      color: "white",
      fontSize: "54px",
      height: "100%",
      padding: "10px 5px 0px 5px",
      width: "100%"
    },
    value: {
      textAlign: "right"
    }
  });

interface HomeAnalyticsCardProps extends WithStyles<typeof styles> {
  icon: React.ReactElement<IconProps>;
  title: string;
  children?: React.ReactNode;
}

const HomeAnalyticsCard = withStyles(styles, { name: "HomeAnalyticsCard" })(
  ({ children, classes, title, icon }: HomeAnalyticsCardProps) => (
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
          <Typography
            className={classes.value}
            color="textPrimary"
            variant="display1"
          >
            {children}
          </Typography>
        </div>
        <div className={classes.iconBackground}>{icon}</div>
      </CardContent>
    </Card>
  )
);
HomeAnalyticsCard.displayName = "HomeAnalyticsCard";
export default HomeAnalyticsCard;
