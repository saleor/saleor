import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import InputAdornment from "@material-ui/core/InputAdornment";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import { SingleAutocompleteSelectField } from "../../../components/SingleAutocompleteSelectField";
import i18n from "../../../i18n";

interface OrderProductAddDialogProps {
  open: boolean;
  variant?: {
    label: string;
    value: string;
  };
  quantity?: number;
  variants?: Array<{
    id: string;
    name: string;
    sku: string;
    stockAllocated;
  }>;
  loading?: boolean;
  fetchVariants(value: string);
  onChange(event: React.ChangeEvent<any>);
  onClose?();
  onConfirm?(event: React.FormEvent<any>);
}

const decorate = withStyles(
  theme => ({
    dialog: {
      overflowY: "visible" as "visible"
    },
    root: {
      display: "grid" as "grid",
      gridColumnGap: theme.spacing.unit * 2 + "px",
      gridTemplateColumns: "1fr 6rem",
      overflowY: "visible" as "visible",
      width: theme.breakpoints.values.sm
    },
    select: {
      flex: 1,
      marginRight: theme.spacing.unit * 2
    },
    textRight: {
      textAlign: "right" as "right"
    }
  }),
  { name: "OrderProductAddDialog" }
);
const OrderProductAddDialog = decorate<OrderProductAddDialogProps>(
  ({
    classes,
    open,
    loading,
    variant,
    variants,
    quantity,
    fetchVariants,
    onChange,
    onClose,
    onConfirm
  }) => {
    const choices =
      !loading && variants
        ? variants.map(v => ({
            label: `${v.sku} ${v.name}`,
            value: v.id
          }))
        : [];
    const maxQuantity =
      !loading && variant && variant.value && variants
        ? variants.filter(v => v.id === variant.value)[0].stockAllocated
        : 0;
    return (
      <Dialog open={open} classes={{ paper: classes.dialog }}>
        <DialogTitle>{i18n.t("Add product")}</DialogTitle>
        <DialogContent className={classes.root}>
          <div className={classes.select}>
            <SingleAutocompleteSelectField
              name="variant"
              value={variant}
              choices={choices}
              onChange={onChange}
              fetchChoices={fetchVariants}
              loading={loading}
            />
          </div>
          <div>
            <TextField
              type="number"
              inputProps={{
                max: maxQuantity,
                style: { textAlign: "right", width: "4rem" }
              }}
              value={quantity}
              onChange={onChange}
              name="quantity"
              error={quantity > maxQuantity}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    {`/ ${maxQuantity}`}
                  </InputAdornment>
                )
              }}
            />
          </div>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>
            {i18n.t("Cancel", { context: "button" })}
          </Button>
          <Button color="primary" variant="raised" onClick={onConfirm}>
            {i18n.t("Confirm", { context: "button" })}
          </Button>
        </DialogActions>
      </Dialog>
    );
  }
);
export default OrderProductAddDialog;
