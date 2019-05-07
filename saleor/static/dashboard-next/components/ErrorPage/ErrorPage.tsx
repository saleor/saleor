import Button from "@material-ui/core/Button";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";
import SVG from "react-inlinesvg";

import * as notFoundImage from "../../../images/what.svg";
import i18n from "../../i18n";

export interface ErrorPageProps extends WithStyles<typeof styles> {
  onBack: () => void;
}

const styles = (theme: Theme) =>
  createStyles({
    bottomHeader: {
      fontWeight: 600 as 600,
      textTransform: "uppercase"
    },
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
      display: "grid",
      gridTemplateColumns: "1fr 487px",
      margin: "0 auto",
      width: 830
    },
    innerContainer: {
      [theme.breakpoints.down("sm")]: {
        order: 1,
        textAlign: "center"
      },
      display: "flex",
      flexDirection: "column",
      justifyContent: "center"
    },
    notFoundImage: {
      "& svg": {
        width: "100%"
      }
    },
    root: {
      alignItems: "center",
      display: "flex",
      height: "calc(100vh - 88px)"
    },
    upperHeader: {
      fontWeight: 600 as 600
    }
  });

const ErrorPage = withStyles(styles, { name: "NotFoundPage" })(
  ({ classes, onBack }: ErrorPageProps) => (
    <div className={classes.root}>
      <div className={classes.container}>
        <div className={classes.innerContainer}>
          <div>
            <Typography className={classes.upperHeader} variant="display1">
              {i18n.t("Ooops!...")}
            </Typography>
            <Typography className={classes.bottomHeader} variant="display2">
              {i18n.t("Error")}
            </Typography>
            <Typography>{i18n.t("We've encountered a problem...")}</Typography>
            <Typography>
              {i18n.t("Don't worry, everything is gonna be fine")}
            </Typography>
          </div>
          <div>
            <Button
              className={classes.button}
              color="primary"
              variant="contained"
              onClick={onBack}
            >
              {i18n.t("Back to home", { context: "button" })}
            </Button>
          </div>
        </div>
        <div>
          <SVG className={classes.notFoundImage} src={notFoundImage} />
        </div>
      </div>
    </div>
  )
);
ErrorPage.displayName = "ErrorPage";
export default ErrorPage;
