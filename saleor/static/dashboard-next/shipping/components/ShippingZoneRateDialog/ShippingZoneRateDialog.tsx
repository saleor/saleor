import Button from "@material-ui/core/Button";
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
import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import ConfirmButton, {
  ConfirmButtonTransitionState
} from "../../../components/ConfirmButton";
import ControlledSwitch from "../../../components/ControlledSwitch";
import Form from "../../../components/Form";
import FormSpacer from "../../../components/FormSpacer";
import Hr from "../../../components/Hr";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { FormErrors, UserError } from "../../../types";
import { ShippingMethodTypeEnum } from "../../../types/globalTypes";
import { ShippingZoneDetailsFragment_shippingMethods } from "../../types/ShippingZoneDetailsFragment";

export interface FormData {
  name: string;
  noLimits: boolean;
  minValue: string;
  maxValue: string;
  isFree: boolean;
  price: string;
}

export interface ShippingZoneRateDialogProps {
  action: "create" | "edit";
  confirmButtonState: ConfirmButtonTransitionState;
  defaultCurrency: string;
  disabled: boolean;
  errors: UserError[];
  open: boolean;
  rate: ShippingZoneDetailsFragment_shippingMethods;
  variant: ShippingMethodTypeEnum;
  onClose: () => void;
  onSubmit: (data: FormData) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    grid: {
      display: "grid",
      gridColumnGap: theme.spacing.unit * 2 + "px",
      gridTemplateColumns: "1fr 1fr"
    },
    subheading: {
      marginBottom: theme.spacing.unit * 2,
      marginTop: theme.spacing.unit * 2
    }
  });
const ShippingZoneRateDialog = withStyles(styles, {
  name: "ShippingZoneRateDialog"
})(
  ({
    action,
    classes,
    confirmButtonState,
    defaultCurrency,
    disabled,
    errors,
    onClose,
    onSubmit,
    open,
    rate,
    variant
  }: ShippingZoneRateDialogProps & WithStyles<typeof styles>) => {
    const initialForm: FormData =
      action === "create"
        ? {
            isFree: false,
            maxValue: "",
            minValue: "",
            name: "",
            noLimits: false,
            price: ""
          }
        : {
            isFree: maybe(() => rate.price.amount === 0, false),
            maxValue:
              variant === ShippingMethodTypeEnum.PRICE
                ? maybe(() => rate.maximumOrderPrice.amount.toString(), "")
                : maybe(() => rate.maximumOrderWeight.value.toString(), ""),
            minValue:
              variant === ShippingMethodTypeEnum.PRICE
                ? maybe(() => rate.minimumOrderPrice.amount.toString(), "")
                : maybe(() => rate.minimumOrderWeight.value.toString(), ""),
            name: maybe(() => rate.name, ""),
            noLimits: false,
            price: maybe(() => rate.price.amount.toString(), "")
          };
    if (action === "edit") {
      initialForm.noLimits = !initialForm.maxValue && !initialForm.minValue;
    }

    return (
      <Dialog open={open} fullWidth maxWidth="sm">
        <Form errors={errors} initial={initialForm} onSubmit={onSubmit}>
          {({ change, data, errors: formErrors, hasChanged }) => {
            const typedFormErrors: FormErrors<
              | "minimumOrderPrice"
              | "minimumOrderWeight"
              | "maximumOrderPrice"
              | "maximumOrderWeight"
              | "price"
              | "name"
            > = formErrors;
            return (
              <>
                <DialogTitle>
                  {variant === ShippingMethodTypeEnum.PRICE
                    ? action === "create"
                      ? i18n.t("Add Price Rate")
                      : i18n.t("Edit Price Rate")
                    : action === "create"
                    ? i18n.t("Add Weight Rate")
                    : i18n.t("Edit Weight Rate")}
                </DialogTitle>
                <DialogContent>
                  <TextField
                    disabled={disabled}
                    error={!!typedFormErrors.name}
                    fullWidth
                    helperText={
                      typedFormErrors.name ||
                      i18n.t("This will be shown to customers at checkout")
                    }
                    label={i18n.t("Rate Name")}
                    name={"name" as keyof FormData}
                    value={data.name}
                    onChange={change}
                  />
                </DialogContent>
                <Hr />
                <DialogContent>
                  {!!variant ? (
                    <>
                      <Typography
                        className={classes.subheading}
                        variant="subheading"
                      >
                        {variant === ShippingMethodTypeEnum.PRICE
                          ? i18n.t("Value range")
                          : i18n.t("Weight range")}
                      </Typography>
                      <ControlledSwitch
                        checked={data.noLimits}
                        name={"noLimits" as keyof FormData}
                        onChange={change}
                        label={
                          <>
                            {i18n.t("There are no value limits")}
                            <Typography variant="caption">
                              {variant === ShippingMethodTypeEnum.PRICE
                                ? i18n.t(
                                    "This rate will apply to all orders of all prices"
                                  )
                                : i18n.t(
                                    "This rate will apply to all orders of all weights"
                                  )}
                            </Typography>
                          </>
                        }
                      />
                      {!data.noLimits && (
                        <>
                          <FormSpacer />
                          <div className={classes.grid}>
                            <TextField
                              disabled={disabled}
                              error={
                                variant === ShippingMethodTypeEnum.PRICE
                                  ? !!typedFormErrors.minimumOrderPrice
                                  : !!typedFormErrors.minimumOrderWeight
                              }
                              fullWidth
                              helperText={
                                variant === ShippingMethodTypeEnum.PRICE
                                  ? typedFormErrors.minimumOrderPrice
                                  : typedFormErrors.minimumOrderWeight
                              }
                              label={
                                variant === ShippingMethodTypeEnum.PRICE
                                  ? typedFormErrors.minimumOrderPrice ||
                                    i18n.t("Minimal Order Value")
                                  : typedFormErrors.minimumOrderWeight ||
                                    i18n.t("Minimal Order Weight")
                              }
                              name={"minValue" as keyof FormData}
                              type="number"
                              value={data.minValue}
                              onChange={change}
                            />
                            <TextField
                              disabled={disabled}
                              error={
                                variant === ShippingMethodTypeEnum.PRICE
                                  ? !!typedFormErrors.maximumOrderPrice
                                  : !!typedFormErrors.maximumOrderWeight
                              }
                              fullWidth
                              helperText={
                                variant === ShippingMethodTypeEnum.PRICE
                                  ? typedFormErrors.maximumOrderPrice
                                  : typedFormErrors.maximumOrderWeight
                              }
                              label={
                                variant === ShippingMethodTypeEnum.PRICE
                                  ? typedFormErrors.maximumOrderPrice ||
                                    i18n.t("Maximal Order Value")
                                  : typedFormErrors.maximumOrderWeight ||
                                    i18n.t("Maximal Order Weight")
                              }
                              name={"maxValue" as keyof FormData}
                              type="number"
                              value={data.maxValue}
                              onChange={change}
                            />
                          </div>
                        </>
                      )}
                    </>
                  ) : (
                    <Skeleton />
                  )}
                </DialogContent>
                <Hr />
                <DialogContent>
                  <Typography
                    className={classes.subheading}
                    variant="subheading"
                  >
                    {i18n.t("Rate")}
                  </Typography>
                  <ControlledSwitch
                    checked={data.isFree}
                    disabled={disabled}
                    label={i18n.t("This is free shipping")}
                    name={"isFree" as keyof FormData}
                    onChange={change}
                  />
                  {!data.isFree && (
                    <>
                      <FormSpacer />
                      <div className={classes.grid}>
                        <TextField
                          disabled={disabled}
                          error={!!typedFormErrors.price}
                          fullWidth
                          helperText={typedFormErrors.price}
                          label={i18n.t("Rate Price")}
                          name={"price" as keyof FormData}
                          type="number"
                          value={data.price}
                          onChange={change}
                          InputProps={{
                            endAdornment: defaultCurrency
                          }}
                        />
                      </div>
                    </>
                  )}
                </DialogContent>
                <DialogActions>
                  <Button onClick={onClose}>
                    {i18n.t("Cancel", { context: "button" })}
                  </Button>
                  <ConfirmButton
                    disabled={disabled || !hasChanged}
                    transitionState={confirmButtonState}
                    color="primary"
                    variant="contained"
                    type="submit"
                  >
                    {action === "create"
                      ? i18n.t("Create rate", { context: "button" })
                      : i18n.t("Update rate", { context: "button" })}
                  </ConfirmButton>
                </DialogActions>
              </>
            );
          }}
        </Form>
      </Dialog>
    );
  }
);
ShippingZoneRateDialog.displayName = "ShippingZoneRateDialog";
export default ShippingZoneRateDialog;
