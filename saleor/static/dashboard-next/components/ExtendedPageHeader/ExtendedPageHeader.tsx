import ArrowBackIcon from "@material-ui/icons/ArrowBack";
import CloseIcon from "@material-ui/icons/Close";
import IconButton from "@material-ui/core/IconButton";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import Skeleton from "../Skeleton";

const decorate = withStyles(theme => ({
  action: {
    flex: "0 0 auto",
    marginRight: theme.spacing.unit * -2
  },
  grid: {
    padding: theme.spacing.unit * 2
  },
  menuButton: {
    flex: "0 0 auto",
    marginLeft: theme.spacing.unit * -2,
    marginRight: theme.spacing.unit * 3
  },
  root: theme.mixins.gutters({
    alignItems: "center",
    display: "flex"
  }),
  subtitle: {
    alignItems: "center" as "center",
    display: "flex",
    marginBottom: theme.spacing.unit * 2
  },
  title: {
    flex: 1,
    paddingBottom: theme.spacing.unit * 2,
    paddingTop: theme.spacing.unit * 2
  }
}));

interface ExtendedPageHeaderProps {
  title?: React.ReactNode;
  onBack?();
}

const ExtendedPageHeader = decorate<ExtendedPageHeaderProps>(
  ({ children, classes, onBack, title }) => (
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
      {title}
      <div className={classes.action}>{children}</div>
    </div>
  )
);

export default ExtendedPageHeader;
