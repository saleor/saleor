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

interface CategoryDeleteDialogProps {
  onClose?();
  onConfirm?();
  opened?: boolean;
}

export const CategoryDeleteDialog: React.StatelessComponent<
  CategoryDeleteDialogProps
> = props => {
  const { children, opened, onConfirm, onClose, ...dialogProps } = props;
  return (
    <Dialog open={opened} {...dialogProps}>
      <DialogTitle>
        {i18n.t("Delete category", { context: "title" })}
      </DialogTitle>
      <DialogContent>{children}</DialogContent>
      <DialogActions>
        <Button color="primary" onClick={onClose}>
          {i18n.t("Cancel", { context: "button" })}
        </Button>
        <Button color="primary" variant="raised" onClick={onConfirm}>
          {i18n.t("Delete category", { context: "button" })}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
