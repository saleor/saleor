import Button from "@material-ui/core/Button";
import Checkbox from "@material-ui/core/Checkbox";
import CircularProgress from "@material-ui/core/CircularProgress";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableRow from "@material-ui/core/TableRow";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import ConfirmButton, {
  ConfirmButtonTransitionState
} from "../../../components/ConfirmButton";
import Debounce from "../../../components/Debounce";
import Form from "../../../components/Form";
import Money from "../../../components/Money";
import TableCellAvatar from "../../../components/TableCellAvatar";
import i18n from "../../../i18n";
import {
  OrderVariantSearch_products_edges_node,
  OrderVariantSearch_products_edges_node_variants
} from "../../types/OrderVariantSearch";

export interface FormData {
  variants: OrderVariantSearch_products_edges_node_variants[];
  query: string;
}

const styles = (theme: Theme) =>
  createStyles({
    avatar: {
      paddingLeft: 0
    },
    content: {
      maxHeight: 600,
      overflowY: "scroll"
    },
    grayText: {
      color: theme.palette.text.disabled
    },
    overflow: {
      overflowY: "visible"
    },
    productCheckboxCell: {
      "&:first-child": {
        paddingLeft: 0,
        paddingRight: 0
      }
    },
    textRight: {
      textAlign: "right"
    },
    variantCheckbox: {
      paddingLeft: theme.spacing.unit
    },
    wideCell: {
      width: "100%"
    }
  });

interface OrderProductAddDialogProps extends WithStyles<typeof styles> {
  confirmButtonState: ConfirmButtonTransitionState;
  open: boolean;
  products: OrderVariantSearch_products_edges_node[];
  loading: boolean;
  onClose: () => void;
  onFetch: (value: string) => void;
  onSubmit: (data: FormData) => void;
}

const initialForm: FormData = {
  query: "",
  variants: []
};

function hasAllVariantsSelected(
  productVariants: OrderVariantSearch_products_edges_node_variants[],
  selectedVariants: OrderVariantSearch_products_edges_node_variants[]
) {
  return productVariants.reduce(
    (acc, productVariant) =>
      acc &&
      !!selectedVariants.find(
        selectedVariant => selectedVariant.id === productVariant.id
      ),
    true
  );
}

const OrderProductAddDialog = withStyles(styles, {
  name: "OrderProductAddDialog"
})(
  ({
    classes,
    confirmButtonState,
    open,
    loading,
    products,
    onFetch,
    onClose,
    onSubmit
  }: OrderProductAddDialogProps) => (
    <Dialog
      open={open}
      classes={{ paper: classes.overflow }}
      fullWidth
      maxWidth="sm"
    >
      <Form initial={initialForm} onSubmit={onSubmit}>
        {({ data, change }) => (
          <>
            <DialogTitle>{i18n.t("Add product")}</DialogTitle>
            <DialogContent className={classes.overflow}>
              <Debounce debounceFn={onFetch}>
                {fetch => (
                  <TextField
                    name="query"
                    value={data.query}
                    onChange={event => change(event, () => fetch(data.query))}
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
                )}
              </Debounce>
            </DialogContent>
            <DialogContent className={classes.content}>
              <Table>
                <TableBody>
                  {products &&
                    products.map(product => (
                      <React.Fragment key={product.id}>
                        <TableRow>
                          <TableCell
                            padding="checkbox"
                            className={classes.productCheckboxCell}
                          >
                            <Checkbox
                              checked={hasAllVariantsSelected(
                                product.variants,
                                data.variants
                              )}
                              onChange={() =>
                                hasAllVariantsSelected(
                                  product.variants,
                                  data.variants
                                )
                                  ? change({
                                      target: {
                                        name: "variants",
                                        value: data.variants.filter(
                                          selectedVariant =>
                                            !product.variants.find(
                                              productVariant =>
                                                productVariant.id ===
                                                selectedVariant.id
                                            )
                                        )
                                      }
                                    } as any)
                                  : change({
                                      target: {
                                        name: "variants",
                                        value: [
                                          ...data.variants,
                                          ...product.variants.filter(
                                            productVariant =>
                                              !data.variants.find(
                                                selectedVariant =>
                                                  selectedVariant.id ===
                                                  productVariant.id
                                              )
                                          )
                                        ]
                                      }
                                    } as any)
                              }
                            />
                          </TableCell>
                          <TableCellAvatar
                            className={classes.avatar}
                            thumbnail={product.thumbnail.url}
                          />
                          <TableCell className={classes.wideCell} colSpan={2}>
                            {product.name}
                          </TableCell>
                        </TableRow>
                        {product.variants.map(variant => (
                          <TableRow key={variant.id}>
                            <TableCell />
                            <TableCell>
                              <Checkbox
                                className={classes.variantCheckbox}
                                checked={
                                  !!data.variants.find(
                                    selectedVariant =>
                                      selectedVariant.id === variant.id
                                  )
                                }
                                onChange={() =>
                                  data.variants.find(
                                    selectedVariant =>
                                      selectedVariant.id === variant.id
                                  )
                                    ? change({
                                        target: {
                                          name: "variants",
                                          value: data.variants.filter(
                                            selectedVariant =>
                                              selectedVariant.id !== variant.id
                                          )
                                        }
                                      } as any)
                                    : change({
                                        target: {
                                          name: "variants",
                                          value: [...data.variants, variant]
                                        }
                                      } as any)
                                }
                              />
                            </TableCell>
                            <TableCell>
                              <div>{variant.name}</div>
                              <div className={classes.grayText}>
                                {i18n.t("SKU {{ sku }}", {
                                  sku: variant.sku
                                })}
                              </div>
                            </TableCell>
                            <TableCell className={classes.textRight}>
                              <Money money={variant.price} />
                            </TableCell>
                          </TableRow>
                        ))}
                      </React.Fragment>
                    ))}
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
                {i18n.t("Confirm", { context: "button" })}
              </ConfirmButton>
            </DialogActions>
          </>
        )}
      </Form>
    </Dialog>
  )
);
OrderProductAddDialog.displayName = "OrderProductAddDialog";
export default OrderProductAddDialog;
