import Button from "@material-ui/core/Button";
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
import React from "react";
import InfiniteScroll from "react-infinite-scroller";

import Checkbox from "@saleor/components/Checkbox";
import ConfirmButton, {
  ConfirmButtonTransitionState
} from "@saleor/components/ConfirmButton";
import Money from "@saleor/components/Money";
import TableCellAvatar from "@saleor/components/TableCellAvatar";
import { ChangeEvent } from "@saleor/hooks/useForm";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";
import {
  SearchOrderVariant_products_edges_node,
  SearchOrderVariant_products_edges_node_variants
} from "../../types/SearchOrderVariant";

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
    loadMoreLoaderContainer: {
      alignItems: "center",
      display: "flex",
      height: theme.spacing.unit * 3,
      justifyContent: "center"
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
      left: theme.spacing.unit,
      position: "relative"
    },
    wideCell: {
      width: "100%"
    }
  });

type SetVariantsAction = (
  data: SearchOrderVariant_products_edges_node_variants[]
) => void;

interface OrderProductAddDialogProps extends WithStyles<typeof styles> {
  confirmButtonState: ConfirmButtonTransitionState;
  open: boolean;
  products: SearchOrderVariant_products_edges_node[];
  loading: boolean;
  hasMore: boolean;
  onClose: () => void;
  onFetch: (value: string) => void;
  onFetchMore: () => void;
  onSubmit: (data: SearchOrderVariant_products_edges_node_variants[]) => void;
}

function hasAllVariantsSelected(
  productVariants: SearchOrderVariant_products_edges_node_variants[],
  selectedVariantsToProductsMap: SearchOrderVariant_products_edges_node_variants[]
): boolean {
  return productVariants.reduce(
    (acc, productVariant) =>
      acc &&
      !!selectedVariantsToProductsMap.find(
        selectedVariant => selectedVariant.id === productVariant.id
      ),
    true
  );
}

function isVariantSelected(
  variant: SearchOrderVariant_products_edges_node_variants,
  selectedVariantsToProductsMap: SearchOrderVariant_products_edges_node_variants[]
): boolean {
  return !!selectedVariantsToProductsMap.find(
    selectedVariant => selectedVariant.id === variant.id
  );
}

const onProductAdd = (
  product: SearchOrderVariant_products_edges_node,
  productIndex: number,
  productsWithAllVariantsSelected: boolean[],
  variants: SearchOrderVariant_products_edges_node_variants[],
  setVariants: SetVariantsAction
) =>
  productsWithAllVariantsSelected[productIndex]
    ? setVariants(
        variants.filter(
          selectedVariant =>
            !product.variants.find(
              productVariant => productVariant.id === selectedVariant.id
            )
        )
      )
    : setVariants([
        ...variants,
        ...product.variants.filter(
          productVariant =>
            !variants.find(
              selectedVariant => selectedVariant.id === productVariant.id
            )
        )
      ]);

const onVariantAdd = (
  variant: SearchOrderVariant_products_edges_node_variants,
  variantIndex: number,
  productIndex: number,
  variants: SearchOrderVariant_products_edges_node_variants[],
  selectedVariantsToProductsMap: boolean[][],
  setVariants: SetVariantsAction
) =>
  selectedVariantsToProductsMap[productIndex][variantIndex]
    ? setVariants(
        variants.filter(selectedVariant => selectedVariant.id !== variant.id)
      )
    : setVariants([...variants, variant]);

function onQueryChange(
  event: ChangeEvent,
  onFetch: (data: string) => void,
  setQuery: (data: string) => void
) {
  const value = event.target.value;

  onFetch(value);
  setQuery(value);
}

const OrderProductAddDialog = withStyles(styles, {
  name: "OrderProductAddDialog"
})(
  ({
    classes,
    confirmButtonState,
    open,
    loading,
    hasMore,
    products,
    onFetch,
    onFetchMore,
    onClose,
    onSubmit
  }: OrderProductAddDialogProps) => {
    const [query, setQuery] = React.useState("");
    const [variants, setVariants] = React.useState<
      SearchOrderVariant_products_edges_node_variants[]
    >([]);

    const selectedVariantsToProductsMap = products
      ? products.map(product =>
          product.variants.map(variant => isVariantSelected(variant, variants))
        )
      : [];
    const productsWithAllVariantsSelected = products
      ? products.map(product =>
          hasAllVariantsSelected(product.variants, variants)
        )
      : [];

    const handleQueryChange = (event: ChangeEvent) =>
      onQueryChange(event, onFetch, setQuery);
    const handleSubmit = () => onSubmit(variants);

    return (
      <Dialog
        onClose={onClose}
        open={open}
        classes={{ paper: classes.overflow }}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle>{i18n.t("Add product")}</DialogTitle>
        <DialogContent className={classes.overflow}>
          <TextField
            name="query"
            value={query}
            onChange={handleQueryChange}
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
        </DialogContent>
        <DialogContent className={classes.content}>
          <InfiniteScroll
            pageStart={0}
            loadMore={onFetchMore}
            hasMore={hasMore}
            useWindow={false}
            loader={
              <div className={classes.loadMoreLoaderContainer}>
                <CircularProgress size={16} />
              </div>
            }
            threshold={10}
          >
            <Table key="table">
              <TableBody>
                {renderCollection(
                  products,
                  (product, productIndex) => (
                    <React.Fragment key={product ? product.id : "skeleton"}>
                      <TableRow>
                        <TableCell
                          padding="checkbox"
                          className={classes.productCheckboxCell}
                        >
                          <Checkbox
                            checked={
                              productsWithAllVariantsSelected[productIndex]
                            }
                            disabled={loading}
                            onChange={() =>
                              onProductAdd(
                                product,
                                productIndex,
                                productsWithAllVariantsSelected,
                                variants,
                                setVariants
                              )
                            }
                          />
                        </TableCell>
                        <TableCellAvatar
                          className={classes.avatar}
                          thumbnail={maybe(() => product.thumbnail.url)}
                        />
                        <TableCell className={classes.wideCell} colSpan={2}>
                          {maybe(() => product.name)}
                        </TableCell>
                      </TableRow>
                      {maybe(() => product.variants, []).map(
                        (variant, variantIndex) => (
                          <TableRow key={variant.id}>
                            <TableCell />
                            <TableCell>
                              <Checkbox
                                className={classes.variantCheckbox}
                                checked={
                                  selectedVariantsToProductsMap[productIndex][
                                    variantIndex
                                  ]
                                }
                                disabled={loading}
                                onChange={() =>
                                  onVariantAdd(
                                    variant,
                                    variantIndex,
                                    productIndex,
                                    variants,
                                    selectedVariantsToProductsMap,
                                    setVariants
                                  )
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
                        )
                      )}
                    </React.Fragment>
                  ),
                  () => (
                    <TableRow>
                      <TableCell colSpan={4}>
                        {i18n.t("No products matching given query")}
                      </TableCell>
                    </TableRow>
                  )
                )}
              </TableBody>
            </Table>
          </InfiniteScroll>
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
            {i18n.t("Confirm", { context: "button" })}
          </ConfirmButton>
        </DialogActions>
      </Dialog>
    );
  }
);
OrderProductAddDialog.displayName = "OrderProductAddDialog";
export default OrderProductAddDialog;
