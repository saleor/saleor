import IconButton from "@material-ui/core/IconButton";
import { withStyles } from "@material-ui/core/styles";
import ArrowBackIcon from "@material-ui/icons/ArrowBack";
import * as classNames from "classnames";
import * as React from "react";

const decorate = withStyles(theme => ({
  action: {
    flex: "0 0 auto"
  },
  grid: {
    padding: theme.spacing.unit * 2
  },
  menuButton: {
    flex: "0 0 auto",
    marginLeft: theme.spacing.unit * -2,
    marginRight: theme.spacing.unit * 3,
    marginTop: -theme.spacing.unit * 2
  },
  root: {
    alignItems: "center",
    display: "flex",
    marginBottom: theme.spacing.unit * 3,
    marginTop: theme.spacing.unit * 3
  },
  subtitle: {
    alignItems: "center" as "center",
    display: "flex",
    marginBottom: theme.spacing.unit * 2
  },
  title: {
    flex: 1,
    paddingBottom: theme.spacing.unit * 2
  }
}));

interface ExtendedPageHeaderProps {
  className?: string;
  title?: React.ReactNode;
  onBack?();
}

const ExtendedPageHeader = decorate<ExtendedPageHeaderProps>(
  ({ children, classes, className, onBack, title }) => (
    <div className={classNames(classes.root, className)}>
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
