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
import React from "react";

import { ChangeEvent } from "@saleor/hooks/useForm";
import { onQueryChange } from "@saleor/misc";
import { SearchCollections_collections_edges_node } from "../../containers/SearchCollections/types/SearchCollections";
import i18n from "../../i18n";
import Checkbox from "../Checkbox";
import ConfirmButton, {
  ConfirmButtonTransitionState
} from "../ConfirmButton/ConfirmButton";
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
  onSubmit: (data: SearchCollections_collections_edges_node[]) => void;
}

function handleCollectionAssign(
  product: SearchCollections_collections_edges_node,
  isSelected: boolean,
  selectedCollections: SearchCollections_collections_edges_node[],
  setSelectedCollections: (
    data: SearchCollections_collections_edges_node[]
  ) => void
) {
  if (isSelected) {
    setSelectedCollections(
      selectedCollections.filter(
        selectedProduct => selectedProduct.id !== product.id
      )
    );
  } else {
    setSelectedCollections([...selectedCollections, product]);
  }
}

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
  }: AssignCollectionDialogProps) => {
    const [query, setQuery] = React.useState("");
    const [selectedCollections, setSelectedCollections] = React.useState<
      SearchCollections_collections_edges_node[]
    >([]);

    const handleQueryChange = (event: ChangeEvent) =>
      onQueryChange(event, onFetch, setQuery);
    const handleSubmit = () => onSubmit(selectedCollections);

    return (
      <Dialog
        onClose={onClose}
        open={open}
        classes={{ paper: classes.overflow }}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle>{i18n.t("Assign Collection")}</DialogTitle>
        <DialogContent className={classes.overflow}>
          <TextField
            name="query"
            value={query}
            onChange={handleQueryChange}
            label={i18n.t("Search Collection", {
              context: "product search input label"
            })}
            placeholder={i18n.t("Search by collection name, etc...", {
              context: "product search input placeholder"
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
              {collections &&
                collections.map(collection => {
                  const isSelected = !!selectedCollections.find(
                    selectedCollection =>
                      selectedCollection.id === collection.id
                  );

                  return (
                    <TableRow key={collection.id}>
                      <TableCell
                        padding="checkbox"
                        className={classes.checkboxCell}
                      >
                        <Checkbox
                          checked={isSelected}
                          onChange={() =>
                            handleCollectionAssign(
                              collection,
                              isSelected,
                              selectedCollections,
                              setSelectedCollections
                            )
                          }
                        />
                      </TableCell>
                      <TableCell className={classes.wideCell}>
                        {collection.name}
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
            onClick={handleSubmit}
          >
            {i18n.t("Assign collections", { context: "button" })}
          </ConfirmButton>
        </DialogActions>
      </Dialog>
    );
  }
);
AssignCollectionDialog.displayName = "AssignCollectionDialog";
export default AssignCollectionDialog;
