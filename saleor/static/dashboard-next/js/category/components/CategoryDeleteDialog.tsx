import Button from "material-ui/Button";
import Dialog, {
  DialogActions,
  DialogContent,
  DialogTitle
} from "material-ui/Dialog";
import Typography from "material-ui/Typography";
import { withStyles } from "material-ui/styles";
import * as React from "react";

import i18n from "../../i18n";

const decorate = withStyles(theme => ({
  deleteButton: {
    backgroundColor: theme.palette.error.main,
    color: theme.palette.error.contrastText,
    "&:hover": {
      backgroundColor: theme.palette.error.main
    }
  }
}));

interface CategoryDeleteDialogProps {
  onClose?();
  onConfirm?();
  opened?: boolean;
}

const CategoryDeleteDialog = decorate<CategoryDeleteDialogProps>(props => {
  const {
    children,
    classes,
    opened,
    onConfirm,
    onClose,
    ...dialogProps
  } = props;
  return (
    <Dialog open={opened} {...dialogProps}>
      <DialogTitle>
        {i18n.t("Delete category", { context: "title" })}
      </DialogTitle>
      <DialogContent>{children}</DialogContent>
      <DialogActions>
        <Button onClick={onClose}>
          {i18n.t("Cancel", { context: "button" })}
        </Button>
        <Button
          className={classes.deleteButton}
          variant="raised"
          onClick={onConfirm}
        >
          {i18n.t("Delete category", { context: "button" })}
        </Button>
      </DialogActions>
    </Dialog>
  );
});

export default CategoryDeleteDialog;
