import IconButton from "@material-ui/core/IconButton";
import Portal from "@material-ui/core/Portal";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import ArrowBackIcon from "@material-ui/icons/ArrowBack";
import * as React from "react";
import AppHeaderContext from "../AppLayout/AppHeaderContext";

export interface AppHeaderProps {
  children: React.ReactNode;
  onBack();
}

const styles = (theme: Theme) =>
  createStyles({
    menuButton: {
      flex: "0 0 auto",
      marginLeft: theme.spacing.unit * -2,
      marginRight: theme.spacing.unit,
      marginTop: -theme.spacing.unit * 2
    },
    root: {
      alignItems: "center",
      color: theme.palette.grey[500],
      display: "flex",
      marginTop: theme.spacing.unit
    },
    title: {
      color: theme.palette.grey[500],
      flex: 1,
      paddingBottom: theme.spacing.unit * 2,
      textTransform: "uppercase"
    }
  });
const AppHeader = withStyles(styles, { name: "AppHeader" })(
  ({
    children,
    classes,
    onBack
  }: AppHeaderProps & WithStyles<typeof styles>) => (
    <AppHeaderContext.Consumer>
      {anchor =>
        anchor ? (
          <Portal container={anchor.current}>
            <div className={classes.root}>
              {onBack && (
                <IconButton
                  color="inherit"
                  className={classes.menuButton}
                  onClick={onBack}
                >
                  <ArrowBackIcon />
                </IconButton>
              )}
              <Typography className={classes.title}>{children}</Typography>
            </div>
          </Portal>
        ) : null
      }
    </AppHeaderContext.Consumer>
  )
);
AppHeader.displayName = "AppHeader";
export default AppHeader;
