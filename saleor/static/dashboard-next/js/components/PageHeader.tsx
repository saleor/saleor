import * as React from "react";
import ArrowBack from "material-ui-icons/ArrowBack";
import Close from "material-ui-icons/Close";
import DeleteIcon from "material-ui-icons/Delete";
import Divider from "material-ui/Divider";
import IconButton from "material-ui/IconButton";
import Skeleton from "./Skeleton";
import Typography from "material-ui/Typography";
import { Link } from "react-router-dom";
import { withStyles } from "material-ui/styles";

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
  backLink?: string;
  cancelLink?: string;
  handleDelete?(event: any);
  title: string;
}

const PageHeader = decorate<PageHeaderProps>(
  ({ backLink, cancelLink, children, classes, handleDelete, title }) => (
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
      {handleDelete && (
        <IconButton color="inherit" onClick={handleDelete}>
          <DeleteIcon />
        </IconButton>
      )}
      <div className={classes.action}>{children}</div>
    </div>
  )
);

export default PageHeader;
