import Button from "@material-ui/core/Button";
import CircularProgress from "@material-ui/core/CircularProgress";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import { createStyles, withStyles, WithStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableRow from "@material-ui/core/TableRow";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import ConfirmButton, {
  ConfirmButtonTransitionState
} from "@saleor/components/ConfirmButton";
import Form from "@saleor/components/Form";
import FormSpacer from "@saleor/components/FormSpacer";
import { maybe, renderCollection } from "@saleor/misc";
import { SearchAttributes_attributes_edges_node } from "../../containers/SearchAttributes/types/SearchAttributes";
import i18n from "../../i18n";
import Checkbox from "../Checkbox";

interface FormData {
  query: string;
}

const styles = createStyles({
  checkboxCell: {
    paddingLeft: 0
  },
  overflow: {
    overflowY: "visible"
  },
  wideCell: {
    width: "100%"
  }
});

export interface AssignAttributeDialogProps {
  confirmButtonState: ConfirmButtonTransitionState;
  open: boolean;
  attributes: SearchAttributes_attributes_edges_node[];
  loading: boolean;
  selected: string[];
  onClose: () => void;
  onFetch: (value: string) => void;
  onSubmit: (data: FormData) => void;
  onToggle: (id: string) => void;
}

const initialForm: FormData = {
  query: ""
};
const AssignAttributeDialog = withStyles(styles, {
  name: "AssignAttributeDialog"
})(
  ({
    attributes,
    classes,
    confirmButtonState,
    loading,
    open,
    selected,
    onClose,
    onFetch,
    onSubmit,
    onToggle
  }: AssignAttributeDialogProps & WithStyles<typeof styles>) => (
    <Dialog
      onClose={onClose}
      open={open}
      classes={{ paper: classes.overflow }}
      fullWidth
      maxWidth="sm"
    >
      <Form initial={initialForm} onSubmit={onSubmit}>
        {({ data, change }) => (
          <>
            <DialogTitle>{i18n.t("Assign Attribute")}</DialogTitle>
            <DialogContent className={classes.overflow}>
              <TextField
                name="query"
                value={data.query}
                onChange={event => change(event, () => onFetch(data.query))}
                label={i18n.t("Search Attributes", {
                  context: "attribute search input label"
                })}
                placeholder={i18n.t("Search by attribute name", {
                  context: "attribute search input placeholder"
                })}
                fullWidth
                InputProps={{
                  autoComplete: "off",
                  endAdornment: loading && <CircularProgress size={16} />
                }}
              />
              <FormSpacer />
              <Table>
                <TableBody>
                  {renderCollection(
                    attributes,
                    attribute => {
                      if (!attribute) {
                        return null;
                      }
                      const isChecked = !!selected.find(
                        selectedAttribute => selectedAttribute === attribute.id
                      );

                      return (
                        <TableRow key={maybe(() => attribute.id)}>
                          <TableCell
                            padding="checkbox"
                            className={classes.checkboxCell}
                          >
                            <Checkbox
                              checked={isChecked}
                              onChange={() => onToggle(attribute.id)}
                            />
                          </TableCell>
                          <TableCell className={classes.wideCell}>
                            {attribute.name}
                          </TableCell>
                        </TableRow>
                      );
                    },
                    () =>
                      !loading && (
                        <TableRow>
                          <TableCell colSpan={2}>
                            {i18n.t("No results found")}
                          </TableCell>
                        </TableRow>
                      )
                  )}
                </TableBody>
              </Table>
            </DialogContent>
            <DialogActions>
              <Button onClick={onClose}>
                {i18n.t("Cancel", { context: "button" })}
              </Button>
              <ConfirmButton
                transitionState={confirmButtonState}
                color="primary"
                variant="contained"
                type="submit"
              >
                {i18n.t("Assign attributes", { context: "button" })}
              </ConfirmButton>
            </DialogActions>
          </>
        )}
      </Form>
    </Dialog>
  )
);
AssignAttributeDialog.displayName = "AssignAttributeDialog";
export default AssignAttributeDialog;
