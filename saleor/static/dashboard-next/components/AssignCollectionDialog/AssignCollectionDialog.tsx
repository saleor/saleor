import Button from "@material-ui/core/Button";
import Checkbox from "@material-ui/core/Checkbox";
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

import { SearchCollections_collections_edges_node } from "../../containers/SearchCollections/types/SearchCollections";
import i18n from "../../i18n";
import ConfirmButton, {
  ConfirmButtonTransitionState
} from "../ConfirmButton/ConfirmButton";
import Debounce from "../Debounce";
import Form from "../Form";
import FormSpacer from "../FormSpacer";

export interface FormData {
  collections: SearchCollections_collections_edges_node[];
  query: string;
}

const styles = createStyles({
  avatar: {
    "&:first-child": {
      paddingLeft: 0
    }
  },
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

interface AssignCollectionDialogProps extends WithStyles<typeof styles> {
  collections: SearchCollections_collections_edges_node[];
  confirmButtonState: ConfirmButtonTransitionState;
  open: boolean;
  loading: boolean;
  onClose: () => void;
  onFetch: (value: string) => void;
  onSubmit: (data: FormData) => void;
}

const initialForm: FormData = {
  collections: [],
  query: ""
};
const AssignCollectionDialog = withStyles(styles, {
  name: "AssignCollectionDialog"
})(
  ({
    classes,
    confirmButtonState,
    open,
    loading,
    collections,
    onClose,
    onFetch,
    onSubmit
  }: AssignCollectionDialogProps) => (
    <Dialog
      open={open}
      classes={{ paper: classes.overflow }}
      fullWidth
      maxWidth="sm"
    >
      <Form initial={initialForm} onSubmit={onSubmit}>
        {({ data, change }) => (
          <>
            <DialogTitle>{i18n.t("Assign Collection")}</DialogTitle>
            <DialogContent className={classes.overflow}>
              <Debounce debounceFn={onFetch}>
                {fetch => (
                  <TextField
                    name="query"
                    value={data.query}
                    onChange={event => change(event, () => fetch(data.query))}
                    label={i18n.t("Search Collection", {
                      context: "product search input label"
                    })}
                    placeholder={i18n.t(
                      "Search by product name, attribute, product type etc...",
                      {
                        context: "product search input placeholder"
                      }
                    )}
                    fullWidth
                    InputProps={{
                      autoComplete: "off",
                      endAdornment: loading && <CircularProgress size={16} />
                    }}
                  />
                )}
              </Debounce>
              <FormSpacer />
              <Table>
                <TableBody>
                  {collections &&
                    collections.map(category => {
                      const isChecked = !!data.collections.find(
                        selectedCollection =>
                          selectedCollection.id === category.id
                      );

                      return (
                        <TableRow key={category.id}>
                          <TableCell
                            padding="checkbox"
                            className={classes.checkboxCell}
                          >
                            <Checkbox
                              checked={isChecked}
                              onChange={() =>
                                isChecked
                                  ? change({
                                      target: {
                                        name: "collections",
                                        value: data.collections.filter(
                                          selectedCollection =>
                                            selectedCollection.id !==
                                            category.id
                                        )
                                      }
                                    } as any)
                                  : change({
                                      target: {
                                        name: "collections",
                                        value: [...data.collections, category]
                                      }
                                    } as any)
                              }
                            />
                          </TableCell>
                          <TableCell className={classes.wideCell}>
                            {category.name}
                          </TableCell>
                        </TableRow>
                      );
                    })}
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
                {i18n.t("Assign collections", { context: "button" })}
              </ConfirmButton>
            </DialogActions>
          </>
        )}
      </Form>
    </Dialog>
  )
);
AssignCollectionDialog.displayName = "AssignCollectionDialog";
export default AssignCollectionDialog;
