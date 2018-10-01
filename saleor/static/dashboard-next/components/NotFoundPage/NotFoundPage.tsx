import Button from "@material-ui/core/Button";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";
import SVG from "react-inlinesvg";

import * as notFoundImage from "../../../images/not-found-404.svg";
import i18n from "../../i18n";

interface NotFoundPageProps {
  onBack: () => void;
}

const decorate = withStyles(theme => ({
  button: {
    marginTop: theme.spacing.unit * 2,
    padding: 20
  },
  container: {
    [theme.breakpoints.down("sm")]: {
      gridTemplateColumns: "1fr",
      padding: theme.spacing.unit * 3,
      width: "100%"
    },
    display: "grid" as "grid",
    gridTemplateColumns: "1fr 487px",
    margin: "0 auto",
    width: 830
  },
  header: {
    fontWeight: 600 as 600
  },
  innerContainer: {
    [theme.breakpoints.down("sm")]: {
      order: 1,
      textAlign: "center" as "center"
    },
    display: "flex" as "flex",
    flexDirection: "column" as "column",
    justifyContent: "center" as "center"
  },
  notFoundImage: {
    "& svg": {
      width: "100%"
    }
  },
  root: {
    alignItems: "center" as "center",
    display: "flex" as "flex",
    height: "100vh",
    width: "100vw"
  }
}));
const NotFoundPage = decorate<NotFoundPageProps>(({ classes, onBack }) => (
  <div className={classes.root}>
    <div className={classes.container}>
      <div className={classes.innerContainer}>
        <div>
          <Typography className={classes.header} variant="display2">
            {i18n.t("Ooops!...")}
          </Typography>
          <Typography className={classes.header} variant="display1">
            {i18n.t("Something's missing")}
          </Typography>
          <Typography>{i18n.t("Sorry the page not found")}</Typography>
        </div>
        <div>
          <Button
            className={classes.button}
            color="secondary"
            variant="contained"
            onClick={onBack}
          >
            {i18n.t("Go back to dashboard", { context: "button" })}
          </Button>
        </div>
      </div>
      <div>
        <SVG className={classes.notFoundImage} src={notFoundImage} />
      </div>
    </div>
  </div>
));
NotFoundPage.displayName = "NotFoundPage";
export default NotFoundPage;
