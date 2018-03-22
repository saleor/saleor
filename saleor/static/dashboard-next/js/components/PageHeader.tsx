import ArrowBackIcon from "material-ui-icons/ArrowBack";
import CloseIcon from "material-ui-icons/Close";
import Divider from "material-ui/Divider";
import IconButton from "material-ui/IconButton";
import { withStyles } from "material-ui/styles";
import Typography from "material-ui/Typography";
import * as React from "react";
import { Link } from "react-router-dom";
import Skeleton from "./Skeleton";

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

interface PageHeaderProps {
  title: string;
  onBack?();
  onCancel?();
}

const PageHeader = decorate<PageHeaderProps>(
  ({ children, classes, onBack, onCancel, title }) => (
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
      {onCancel && (
        <IconButton
          color="inherit"
          className={classes.menuButton}
          onClick={onCancel}
        >
          <CloseIcon />
        </IconButton>
      )}
      <Typography className={classes.title} variant="title">
        {title !== undefined ? title : <Skeleton style={{ width: "10em" }} />}
      </Typography>
      <div className={classes.action}>{children}</div>
    </div>
  )
);

export default PageHeader;
