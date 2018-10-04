import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import InputAdornment from "@material-ui/core/InputAdornment";
import { withStyles, WithStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import Form from "../../../components/Form";
import { SingleAutocompleteSelectField } from "../../../components/SingleAutocompleteSelectField";
import i18n from "../../../i18n";

export interface FormData {
  quantity: number;
  variant: {
    label: string;
    value: string;
  };
}

interface OrderProductAddDialogProps {
  open: boolean;
  variants?: Array<{
    id: string;
    name: string;
    sku: string;
    stockQuantity: number;
  }>;
  loading: boolean;
  fetchVariants: (value: string) => void;
  onClose: () => void;
  onSubmit: (data: FormData) => void;
}

interface OrderProductAddDialogState {
  maxQuantity: number;
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
const initialForm: FormData = {
  quantity: 0,
  variant: {
    label: "",
    value: ""
  }
};
const OrderProductAddDialog = decorate<OrderProductAddDialogProps>(
  class OrderProductAddDialogComponent extends React.Component<
    OrderProductAddDialogProps &
      WithStyles<"dialog" | "root" | "select" | "textRight">
  > {
    state: OrderProductAddDialogState = { maxQuantity: 0 };
    render() {
      const {
        classes,
        open,
        loading,
        variants,
        fetchVariants,
        onClose,
        onSubmit
      } = this.props;
      return (
        <Dialog open={open} classes={{ paper: classes.dialog }}>
          <Form initial={initialForm} onSubmit={onSubmit}>
            {({ data, change }) => {
              const choices =
                !loading && variants
                  ? variants.map(v => ({
                      label: `${v.sku} ${v.name}`,
                      value: v.id
                    }))
                  : [];
              const handleSelect = (event: React.ChangeEvent<any>) => {
                this.setState({
                  maxQuantity: variants.filter(
                    v => v.id === event.target.value.value
                  )[0].stockQuantity
                });
                change(event);
              };
              return (
                <>
                  <DialogTitle>{i18n.t("Add product")}</DialogTitle>
                  <DialogContent className={classes.root}>
                    <div className={classes.select}>
                      <SingleAutocompleteSelectField
                        name="variant"
                        value={data.variant}
                        choices={choices}
                        onChange={handleSelect}
                        fetchChoices={fetchVariants}
                        loading={loading}
                      />
                    </div>
                    <div>
                      <TextField
                        type="number"
                        inputProps={{
                          max: this.state.maxQuantity,
                          style: { textAlign: "right", width: "4rem" }
                        }}
                        value={data.quantity}
                        onChange={change}
                        name="quantity"
                        error={data.quantity > this.state.maxQuantity}
                        InputProps={{
                          endAdornment: (
                            <InputAdornment position="end">
                              {`/ ${this.state.maxQuantity}`}
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
                    <Button color="primary" variant="raised" type="submit">
                      {i18n.t("Confirm", { context: "button" })}
                    </Button>
                  </DialogActions>
                </>
              );
            }}
          </Form>
        </Dialog>
      );
    }
  }
);
export default OrderProductAddDialog;
