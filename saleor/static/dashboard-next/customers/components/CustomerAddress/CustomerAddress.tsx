import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardActions from "@material-ui/core/CardActions";
import CardContent from "@material-ui/core/CardContent";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import AddressFormatter from "../../../components/AddressFormatter";
import CardMenu from "../../../components/CardMenu";
import CardTitle from "../../../components/CardTitle";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { AddressTypeEnum } from "../../../types/globalTypes";
import { CustomerAddresses_user_addresses } from "../../types/CustomerAddresses";

export interface CustomerAddressProps {
  address: CustomerAddresses_user_addresses;
  disabled: boolean;
  isDefaultBillingAddress: boolean;
  isDefaultShippingAddress: boolean;
  addressNumber: number;
  onEdit: () => void;
  onRemove: () => void;
  onSetAsDefault: (type: AddressTypeEnum) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    actions: {
      flexDirection: "row"
    }
  });
const CustomerAddress = withStyles(styles, { name: "CustomerAddress" })(
  ({
    address,
    addressNumber,
    classes,
    disabled,
    isDefaultBillingAddress,
    isDefaultShippingAddress,
    onEdit,
    onRemove,
    onSetAsDefault
  }: CustomerAddressProps & WithStyles<typeof styles>) => (
    <Card>
      <CardTitle
        title={
          address ? (
            <>
              {i18n.t("Address {{ addressNumber }}", {
                addressNumber
              })}
              <Typography variant="caption">
                {isDefaultBillingAddress && isDefaultShippingAddress
                  ? i18n.t("Default Address")
                  : isDefaultShippingAddress
                  ? i18n.t("Default Shipping Address")
                  : isDefaultBillingAddress
                  ? i18n.t("Default Billing Address")
                  : null}
              </Typography>
            </>
          ) : (
            <Skeleton />
          )
        }
        height="const"
        toolbar={
          <CardMenu
            disabled={disabled}
            menuItems={[
              {
                label: i18n.t("Set as default shipping address", {
                  context: "button"
                }),
                onSelect: () => onSetAsDefault(AddressTypeEnum.SHIPPING)
              },
              {
                label: i18n.t("Set as default billing address", {
                  context: "button"
                }),
                onSelect: () => onSetAsDefault(AddressTypeEnum.BILLING)
              }
            ]}
          />
        }
      />
      <CardContent>
        <AddressFormatter address={address} />
      </CardContent>
      <CardActions className={classes.actions}>
        <Button
          color="secondary"
          disabled={disabled}
          variant="flat"
          onClick={onEdit}
        >
          {i18n.t("Edit")}
        </Button>
        <Button
          color="secondary"
          disabled={disabled}
          variant="flat"
          onClick={onRemove}
        >
          {i18n.t("Delete")}
        </Button>
      </CardActions>
    </Card>
  )
);
CustomerAddress.displayName = "CustomerAddress";
export default CustomerAddress;
