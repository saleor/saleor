import Button from "material-ui/Button";
import Dialog, {
  DialogActions,
  DialogContent,
  DialogTitle
} from "material-ui/Dialog";
import Typography from "material-ui/Typography";
import { withStyles } from "material-ui/styles";
import * as React from "react";

import { pgettext } from "../../i18n";

interface CategoryDeleteDialogProps {
  onClose?();
  onConfirm?();
  opened?: boolean;
  title: string;
}

export const CategoryDeleteDialog: React.StatelessComponent<
  CategoryDeleteDialogProps
> = props => {
  const { title, children, opened, onConfirm, onClose, ...dialogProps } = props;
  return (
    <Dialog open={opened} {...dialogProps}>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>{children}</DialogContent>
      <DialogActions>
        <Button color="primary" onClick={onClose}>
          {pgettext("Dashboard cancel action", "Cancel")}
        </Button>
        <Button color="primary" variant="raised" onClick={onConfirm}>
          {pgettext("Dashboard delete action", "Remove")}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
