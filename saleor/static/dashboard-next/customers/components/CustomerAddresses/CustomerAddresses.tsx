import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import AddressFormatter from "../../../components/AddressFormatter/AddressFormatter";
import CardTitle from "../../../components/CardTitle";
import { Hr } from "../../../components/Hr";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { CustomerDetails_user } from "../../types/CustomerDetails";

const styles = (theme: Theme) =>
  createStyles({
    label: {
      fontWeight: 600,
      marginBottom: theme.spacing.unit
    }
  });

export interface CustomerAddressesProps extends WithStyles<typeof styles> {
  customer: CustomerDetails_user;
  disabled: boolean;
  onAddressManageClick: () => void;
}

const CustomerAddresses = withStyles(styles, { name: "CustomerAddresses" })(
  ({
    classes,
    customer,
    disabled,
    onAddressManageClick
  }: CustomerAddressesProps) => (
    <Card>
      <CardTitle
        title={i18n.t("Address Information")}
        toolbar={
          <Button
            color="primary"
            disabled={disabled}
            variant="text"
            onClick={onAddressManageClick}
          >
            {i18n.t("Manage", { context: "button" })}
          </Button>
        }
      />
      {maybe(() => customer.defaultBillingAddress.id) !==
      maybe(() => customer.defaultShippingAddress.id) ? (
        <>
          {maybe(() => customer.defaultBillingAddress) !== null && (
            <CardContent>
              <Typography className={classes.label}>
                {i18n.t("Billing address")}
              </Typography>
              <AddressFormatter
                address={maybe(() => customer.defaultBillingAddress)}
              />
            </CardContent>
          )}
          {maybe(
            () =>
              customer.defaultBillingAddress && customer.defaultShippingAddress
          ) && <Hr />}
          {maybe(() => customer.defaultShippingAddress) && (
            <CardContent>
              <Typography className={classes.label}>
                {i18n.t("Shipping address")}
              </Typography>
              <AddressFormatter
                address={maybe(() => customer.defaultShippingAddress)}
              />
            </CardContent>
          )}
        </>
      ) : maybe(() => customer.defaultBillingAddress) === null &&
        maybe(() => customer.defaultShippingAddress) === null ? (
        <CardContent>
          <Typography>
            {i18n.t("This customer has no addresses yet")}
          </Typography>
        </CardContent>
      ) : (
        <CardContent>
          <Typography className={classes.label}>{i18n.t("Address")}</Typography>
          <AddressFormatter
            address={maybe(() => customer.defaultBillingAddress)}
          />
        </CardContent>
      )}
    </Card>
  )
);
CustomerAddresses.displayName = "CustomerAddresses";
export default CustomerAddresses;
