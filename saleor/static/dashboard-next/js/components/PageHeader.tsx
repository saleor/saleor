import Divider from "material-ui/Divider";
import IconButton from "material-ui/IconButton";
import Toolbar from "material-ui/Toolbar";
import Typography from "material-ui/Typography";
import { withStyles } from "material-ui/styles";
import ArrowBack from "material-ui-icons/ArrowBack";
import Close from "material-ui-icons/Close";
import * as React from "react";
import { Link } from "react-router-dom";
import Skeleton from "./Skeleton";

const decorate = withStyles(theme => ({
  grid: {
    padding: theme.spacing.unit * 2
  },
  menuButton: {
    marginRight: theme.spacing.unit * 2
  },
  title: {
    flex: 1
  },
  toolbar: {
    backgroundColor: theme.palette.background.paper
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
    <Toolbar className={classes.toolbar}>
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
      {children}
    </Toolbar>
  )
);

export default PageHeader;
