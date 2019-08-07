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

import ConfirmButton, {
  ConfirmButtonTransitionState
} from "@saleor/components/ConfirmButton";
import FormSpacer from "@saleor/components/FormSpacer";
import useSearchQuery from "@saleor/hooks/useSearchQuery";
import { SearchCategories_categories_edges_node } from "../../containers/SearchCategories/types/SearchCategories";
import i18n from "../../i18n";
import Checkbox from "../Checkbox";

export interface FormData {
  categories: SearchCategories_categories_edges_node[];
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

interface AssignCategoriesDialogProps extends WithStyles<typeof styles> {
  categories: SearchCategories_categories_edges_node[];
  confirmButtonState: ConfirmButtonTransitionState;
  open: boolean;
  loading: boolean;
  onClose: () => void;
  onFetch: (value: string) => void;
  onSubmit: (data: SearchCategories_categories_edges_node[]) => void;
}

function handleCategoryAssign(
  product: SearchCategories_categories_edges_node,
  isSelected: boolean,
  selectedCategories: SearchCategories_categories_edges_node[],
  setSelectedCategories: (
    data: SearchCategories_categories_edges_node[]
  ) => void
) {
  if (isSelected) {
    setSelectedCategories(
      selectedCategories.filter(
        selectedProduct => selectedProduct.id !== product.id
      )
    );
  } else {
    setSelectedCategories([...selectedCategories, product]);
  }
}

const AssignCategoriesDialog = withStyles(styles, {
  name: "AssignCategoriesDialog"
})(
  ({
    classes,
    confirmButtonState,
    open,
    loading,
    categories: categories,
    onClose,
    onFetch,
    onSubmit
  }: AssignCategoriesDialogProps) => {
    const [query, onQueryChange] = useSearchQuery(onFetch);
    const [selectedCategories, setSelectedCategories] = React.useState<
      SearchCategories_categories_edges_node[]
    >([]);

    const handleSubmit = () => onSubmit(selectedCategories);

    return (
      <Dialog
        open={open}
        onClose={onClose}
        classes={{ paper: classes.overflow }}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle>{i18n.t("Assign Categories")}</DialogTitle>
        <DialogContent className={classes.overflow}>
          <TextField
            name="query"
            value={query}
            onChange={onQueryChange}
            label={i18n.t("Search Categories", {
              context: "category search input label"
            })}
            placeholder={i18n.t("Search by category name, etc...", {
              context: "category search input placeholder"
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
              {categories &&
                categories.map(category => {
                  const isSelected = !!selectedCategories.find(
                    selectedCategories => selectedCategories.id === category.id
                  );

                  return (
                    <TableRow key={category.id}>
                      <TableCell
                        padding="checkbox"
                        className={classes.checkboxCell}
                      >
                        <Checkbox
                          checked={isSelected}
                          onChange={() =>
                            handleCategoryAssign(
                              category,
                              isSelected,
                              selectedCategories,
                              setSelectedCategories
                            )
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
            onClick={handleSubmit}
          >
            {i18n.t("Assign categories", { context: "button" })}
          </ConfirmButton>
        </DialogActions>
      </Dialog>
    );
  }
);
AssignCategoriesDialog.displayName = "AssignCategoriesDialog";
export default AssignCategoriesDialog;
