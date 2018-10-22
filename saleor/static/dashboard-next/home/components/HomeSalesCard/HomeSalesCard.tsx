import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import i18n from "../../../i18n";

import Dollar from "@material-ui/icons/AttachMoney";
import * as React from "react";

import Money from "../../../components/Money";
import Skeleton from "../../../components/Skeleton";

interface MoneyType {
  amount: number;
  currency: string;
}

interface HomeSalesCardProps {
  disabled: boolean;
  title: string;
  daily: {
    sales: MoneyType;
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
    marginRight: `${theme.spacing.unit * 1.5}px`,
    [theme.breakpoints.down("sm")]: {
      marginRight: `${theme.spacing.unit * 0.5}px`
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
const HomeSalesCard = decorate<HomeSalesCardProps>(
  ({ classes, title, daily }) => {
    return (
      <Card className={classes.fullWidth}>
        <CardContent className={classes.cardContent}>
          <div>
            <Typography className={classes.cardTitle} variant="subheading">
              {title}
            </Typography>
            <Typography className={classes.cardSubtitle} variant="caption">
              {i18n.t("Today")}
            </Typography>
            <Typography color={"textPrimary"} variant="headline">
              {daily &&
              daily.sales &&
              daily.sales.amount !== undefined &&
              daily.sales.currency !== undefined ? (
                <Money
                  amount={daily.sales.amount}
                  currency={daily.sales.currency}
                />
              ) : (
                <Skeleton />
              )}
            </Typography>
          </div>
          <div className={classes.iconBackground}>
            <Dollar className={classes.icon} />
          </div>
        </CardContent>
      </Card>
    );
  }
);
export default HomeSalesCard;
