import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import LocalShipping from "@material-ui/icons/LocalShipping";
import * as React from "react";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

interface HomeOrdersCardProps {
  disabled: boolean;
  title: string;
  daily: {
    orders: {
      amount: number;
    };
  };
}

const decorate = withStyles(theme => ({
  cardContent: {
    "&:last-child": {
      paddingBottom: 16
    },
    display: "grid" as "grid",
    gridColumnGap: theme.spacing.unit * 1 + "px",
    gridTemplateColumns: "minmax(min-content, 5fr) 70px"
  },
  cardSubtitle: {
    color: theme.palette.text.secondary,
    fontSize: ".65rem",
    height: "16px",
    lineHeight: 0.5
  },
  cardTitle: {
    fontWeight: "bold" as "bold"
  },
  fullWidth: {
    marginLeft: `${theme.spacing.unit * 1.5}px`,
    [theme.breakpoints.down("sm")]: {
      marginLeft: `${theme.spacing.unit * 0.5}px`
    },
    overflow: "initial" as "initial",
    width: "100%"
  },
  icon: {
    color: theme.palette.primary.contrastText,
    fontSize: 54,
    margin: ".5rem .3rem"
  },
  iconBackground: {
    alignSelf: "center",
    backgroundColor: theme.palette.primary.main,
    borderRadius: "5px",
    justifySelf: "center"
  }
}));
const HomeOrdersCard = decorate<HomeOrdersCardProps>(
  ({ classes, title, daily }) => {
    return (
      <Card className={classes.fullWidth}>
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
              {daily && daily.orders ? daily.orders.amount : <Skeleton />}
            </Typography>
          </div>
          <div className={classes.iconBackground}>
            <LocalShipping className={classes.icon} />
          </div>
        </CardContent>
      </Card>
    );
  }
);
export default HomeOrdersCard;
