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
import Skeleton from "../Skeleton";

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
      "&:hover": {
        color: theme.typography.body1.color
      },
      alignItems: "center",
      color: theme.palette.grey[500],
      cursor: "pointer",
      display: "flex",
      marginTop: theme.spacing.unit / 2,
      transition: theme.transitions.duration.standard + "ms"
    },
    skeleton: {
      marginBottom: theme.spacing.unit * 2,
      width: "10rem"
    },
    title: {
      color: "inherit",
      flex: 1,
      marginLeft: theme.spacing.unit,
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
            <div className={classes.root} onClick={onBack}>
              <ArrowBackIcon />
              {children ? (
                <Typography className={classes.title}>{children}</Typography>
              ) : (
                <Skeleton className={classes.skeleton} />
              )}
            </div>
          </Portal>
        ) : null
      }
    </AppHeaderContext.Consumer>
  )
);
AppHeader.displayName = "AppHeader";
export default AppHeader;
