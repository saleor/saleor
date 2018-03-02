import * as React from "react";
import Button from "material-ui/Button";
import Modal from "material-ui/Modal";
import Typography from "material-ui/Typography";
import Card, { CardContent, CardActions } from "material-ui/Card";
import { withStyles } from "material-ui/styles";

import { pgettext } from "../i18n";

const decorate = withStyles(theme => ({
  card: {
    outline: "none",
    top: "40%",
    left: "calc(50% - 17rem)",
    position: "absolute" as "absolute",
    width: "35rem",
    fontSize: theme.typography.body1.fontSize
  },
  cardActions: {
    margin: 0,
    flexDirection: "row-reverse" as "row-reverse"
  },
  title: {
    marginBottom: theme.spacing.unit * 4,
    textTransform: "uppercase"
  },
  button: {
    marginLeft: theme.spacing.unit / 2
  }
}));

interface ConfirmRemovalProps {
  onClose?();
  onConfirm?();
  opened?: boolean;
  title: string;
}

export const ConfirmRemoval = decorate<ConfirmRemovalProps>(props => {
  const {
    title,
    children,
    classes,
    opened,
    onConfirm,
    onClose,
    ...modalProps
  } = props;
  return (
    <Modal open={opened} {...modalProps}>
      <Card className={classes.card}>
        <CardContent>
          <Typography variant="title" className={classes.title}>
            {title}
          </Typography>
          {children}
        </CardContent>
        <CardActions className={classes.cardActions}>
          <Button
            color="secondary"
            variant="raised"
            onClick={onConfirm}
            className={classes.button}
          >
            {pgettext("Dashboard delete action", "Remove")}
          </Button>
          <Button
            color="secondary"
            onClick={onClose}
            className={classes.button}
          >
            {pgettext("Dashboard cancel action", "Cancel")}
          </Button>
        </CardActions>
      </Card>
    </Modal>
  );
});
