import Divider from "material-ui/Divider";
import IconButton from "material-ui/IconButton";
import Toolbar from "material-ui/Toolbar";
import Typography from "material-ui/Typography";
import { withStyles } from "material-ui/styles";
import ArrowBack from "material-ui-icons/ArrowBack";
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
  loading?: boolean;
  title: string;
}

export const PageHeader = decorate<PageHeaderProps>(
  ({ backLink, children, classes, loading, title }) => (
    <>
      <Toolbar className={classes.toolbar}>
        {backLink && (
          <IconButton
            color="inherit"
            className={classes.menuButton}
            component={props => <Link to={backLink} {...props} />}
            disabled={loading}
          >
            <ArrowBack />
          </IconButton>
        )}
        <Typography className={classes.title} variant="title">
          {title || (loading && <Skeleton style={{ width: "10em" }} />) || ""}
        </Typography>
        {children}
      </Toolbar>
      <Divider />
    </>
  )
);

export default PageHeader;
