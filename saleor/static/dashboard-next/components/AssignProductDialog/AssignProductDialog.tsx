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
import TableCellAvatar from "@saleor/components/TableCellAvatar";
import useSearchQuery from "@saleor/hooks/useSearchQuery";
import { SearchProducts_products_edges_node } from "../../containers/SearchProducts/types/SearchProducts";
import i18n from "../../i18n";
import { maybe } from "../../misc";
import Checkbox from "../Checkbox";

export interface FormData {
  products: SearchProducts_products_edges_node[];
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

interface AssignProductDialogProps extends WithStyles<typeof styles> {
  confirmButtonState: ConfirmButtonTransitionState;
  open: boolean;
  products: SearchProducts_products_edges_node[];
  loading: boolean;
  onClose: () => void;
  onFetch: (value: string) => void;
  onSubmit: (data: SearchProducts_products_edges_node[]) => void;
}

function handleProductAssign(
  product: SearchProducts_products_edges_node,
  isSelected: boolean,
  selectedProducts: SearchProducts_products_edges_node[],
  setSelectedProducts: (data: SearchProducts_products_edges_node[]) => void
) {
  if (isSelected) {
    setSelectedProducts(
      selectedProducts.filter(
        selectedProduct => selectedProduct.id !== product.id
      )
    );
  } else {
    setSelectedProducts([...selectedProducts, product]);
  }
}

const AssignProductDialog = withStyles(styles, {
  name: "AssignProductDialog"
})(
  ({
    classes,
    confirmButtonState,
    open,
    loading,
    products,
    onClose,
    onFetch,
    onSubmit
  }: AssignProductDialogProps) => {
    const [query, onQueryChange] = useSearchQuery(onFetch);
    const [selectedProducts, setSelectedProducts] = React.useState<
      SearchProducts_products_edges_node[]
    >([]);

    const handleSubmit = () => onSubmit(selectedProducts);

    return (
      <Dialog
        onClose={onClose}
        open={open}
        classes={{ paper: classes.overflow }}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle>{i18n.t("Assign Product")}</DialogTitle>
        <DialogContent className={classes.overflow}>
          <TextField
            name="query"
            value={query}
            onChange={onQueryChange}
            label={i18n.t("Search Products", {
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
          <FormSpacer />
          <Table>
            <TableBody>
              {products &&
                products.map(product => {
                  const isSelected = !!selectedProducts.find(
                    selectedProduct => selectedProduct.id === product.id
                  );

                  return (
                    <TableRow key={product.id}>
                      <TableCellAvatar
                        className={classes.avatar}
                        thumbnail={maybe(() => product.thumbnail.url)}
                      />
                      <TableCell className={classes.wideCell}>
                        {product.name}
                      </TableCell>
                      <TableCell
                        padding="checkbox"
                        className={classes.checkboxCell}
                      >
                        <Checkbox
                          checked={isSelected}
                          onChange={() =>
                            handleProductAssign(
                              product,
                              isSelected,
                              selectedProducts,
                              setSelectedProducts
                            )
                          }
                        />
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
            {i18n.t("Assign products", { context: "button" })}
          </ConfirmButton>
        </DialogActions>
      </Dialog>
    );
  }
);
AssignProductDialog.displayName = "AssignProductDialog";
export default AssignProductDialog;
