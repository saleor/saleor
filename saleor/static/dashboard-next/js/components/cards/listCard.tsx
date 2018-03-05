import * as React from "react";
import Button from "material-ui/Button";
import Card, { CardContent } from "material-ui/Card";
import Typography from "material-ui/Typography";
import { withStyles } from "material-ui/styles";

import { Table } from "../table";
import { gettext } from "../../i18n";

const decorate = withStyles(theme => ({
  listCard: {
    paddingBottom: 0
  },
  listCardActions: {
    paddingBottom: 0
  },
  listCardAddActionButton: {
    margin: "1rem 0"
  }
}));

interface ListCardProps {
  addActionLabel: string;
  displayLabel: boolean;
  handleAddAction();
  label: string;
}

export const ListCard = decorate<ListCardProps>(
  ({
    addActionLabel,
    children,
    classes,
    displayLabel,
    handleAddAction,
    label
  }) => (
    <Card className={classes.listCard}>
      <div>
        {displayLabel && (
          <CardContent className={classes.listCardActions}>
            <Typography variant="display1">{label}</Typography>
            <Button
              color="secondary"
              onClick={handleAddAction}
              className={classes.listCardAddActionButton}
            >
              {addActionLabel}
            </Button>
          </CardContent>
        )}
        <CardContent
          style={{
            borderTop: "none",
            padding: 0
          }}
        >
          {children}
        </CardContent>
      </div>
    </Card>
  )
);
ListCard.defaultProps = {
  addActionLabel: gettext("Add"),
  displayLabel: false
};
