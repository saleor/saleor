import Button from "material-ui/Button";
import Paper from "material-ui/Paper";
import Toolbar from "material-ui/Toolbar";
import Typography from "material-ui/Typography";
import { withStyles } from "material-ui/styles";
import * as React from "react";
import { Link } from "react-router-dom";

import { gettext } from "../../i18n";

const decorate = withStyles(theme => ({
  spacer: {
    flex: "1 1 100%"
  },
  actions: {
    whiteSpace: "nowrap",
    minWidth: "auto"
  },
  title: {
    flex: "0 0 auto"
  }
}));

interface ListCardProps {
  addActionLabel: string;
  addActionLink: string;
  label: string;
}

export const CategoryListCard = decorate<ListCardProps>(
  ({ addActionLabel, addActionLink, children, classes, label }) => (
    <Paper>
      <Toolbar>
        <div className={classes.title}>
          <Typography variant="title">{label}</Typography>
        </div>
        <div className={classes.spacer} />
        <Button
          className={classes.actions}
          color="primary"
          component={props => <Link to={addActionLink} {...props} />}
        >
          {addActionLabel}
        </Button>
      </Toolbar>
      {children}
    </Paper>
  )
);

export default CategoryListCard;
