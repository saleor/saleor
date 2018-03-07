import * as React from "react";
import Typography from "material-ui/Typography";
import { withStyles } from "material-ui/styles";

import { Table } from "../table";
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
  handleAddAction();
  label: string;
}

export const ListCard = decorate<ListCardProps>(
  ({ addActionLabel, children, classes, handleAddAction, label }) => (
    <Paper>
      <Toolbar>
        <div className={classes.title}>
          <Typography variant="title">{label}</Typography>
        </div>
        <div className={classes.spacer} />
        <Button
          className={classes.actions}
          color="primary"
          onClick={handleAddAction}
        >
          {addActionLabel}
        </Button>
      </Toolbar>
      {children}
    </Paper>
  )
);

export default ListCard;
