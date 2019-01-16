import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogContentText from "@material-ui/core/DialogContentText";
import DialogTitle from "@material-ui/core/DialogTitle";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import * as React from "react";

import i18n from "../../../i18n";

const styles = (theme: Theme) =>
  createStyles({
    deleteButton: {
      "&:hover": {
        backgroundColor: theme.palette.error.main
      },
      backgroundColor: theme.palette.error.main,
      color: theme.palette.error.contrastText
    }
  });

export interface CategoryDeleteDialogProps extends WithStyles<typeof styles> {
  open: boolean;
  name: string;
  onClose();
  onConfirm();
}

const CategoryDeleteDialog = withStyles(styles, {
  name: "CategoryDeleteDialog"
})(({ classes, name, open, onConfirm, onClose }: CategoryDeleteDialogProps) => (
  <Dialog open={open}>
    <DialogTitle>{i18n.t("Delete category", { context: "title" })}</DialogTitle>
    <DialogContent>
      <DialogContentText
        dangerouslySetInnerHTML={{
          __html: i18n.t(
            "Are you sure you want to remove <strong>{{name}}</strong>?",
            { name }
          )
        }}
      />
    </DialogContent>
    <DialogActions>
      <Button onClick={onClose}>
        {i18n.t("Cancel", { context: "button" })}
      </Button>
      <Button
        className={classes.deleteButton}
        variant="contained"
        onClick={onConfirm}
      >
        {i18n.t("Delete category", { context: "button" })}
      </Button>
    </DialogActions>
  </Dialog>
));
CategoryDeleteDialog.displayName = "CategoryDeleteDialog";
export default CategoryDeleteDialog;
