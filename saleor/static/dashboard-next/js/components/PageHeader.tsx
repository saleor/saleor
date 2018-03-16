import Divider from "material-ui/Divider";
import IconButton from "material-ui/IconButton";
import Typography from "material-ui/Typography";
import { withStyles } from "material-ui/styles";
import ArrowBack from "material-ui-icons/ArrowBack";
import Close from "material-ui-icons/Close";
import * as React from "react";
import { Link } from "react-router-dom";
import Skeleton from "./Skeleton";

const decorate = withStyles(theme => ({
  root: theme.mixins.gutters({
    display: "flex",
    alignItems: "center"
  }),
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
  title: {
    flex: 1,
    paddingBottom: theme.spacing.unit * 2,
    paddingTop: theme.spacing.unit * 2
  },
  subtitle: {
    display: "flex",
    alignItems: "center" as "center",
    marginBottom: theme.spacing.unit * 2
  }
}));

interface PageHeaderProps {
  backLink?: string;
  cancelLink?: string;
  title: string;
}

const PageHeader = decorate<PageHeaderProps>(
  ({ backLink, cancelLink, children, classes, title }) => (
    <div className={classes.root}>
      {backLink && (
        <IconButton
          color="inherit"
          className={classes.menuButton}
          component={props => <Link to={backLink} {...props} />}
          disabled={backLink === "#"}
        >
          <ArrowBack />
        </IconButton>
      )}
      {cancelLink && (
        <IconButton
          color="inherit"
          className={classes.menuButton}
          component={props => <Link to={cancelLink} {...props} />}
          disabled={cancelLink === "#"}
        >
          <Close />
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
