import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import DialogContentText from "@material-ui/core/DialogContentText";
import ActionDialog from "../../../components/ActionDialog";
import i18n from "../../../i18n";

const decorate = withStyles({});

interface CategoryDeleteProps {
  open: boolean;
  title: string;
  dialogText: string;
  onClose: () => any;
  onConfirm?(event: React.FormEvent<any>);
}

const CategoryDelete = decorate<CategoryDeleteProps>(
  ({ open, onClose, onConfirm, title, dialogText }) => (
    <ActionDialog
      open={open}
      onClose={onClose}
      onConfirm={onConfirm}
      variant="delete"
      title={i18n.t(title)}
    >
      <DialogContentText>{i18n.t(dialogText)}</DialogContentText>
    </ActionDialog>
  )
);

export default CategoryDelete;
