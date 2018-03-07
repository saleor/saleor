import * as React from "react";
import Typography from "material-ui/Typography";
import { Link } from "react-router-dom";
import { withStyles } from "material-ui/styles";

import { gettext } from "../../i18n";
import { Button, Toolbar, Paper } from "material-ui";

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
