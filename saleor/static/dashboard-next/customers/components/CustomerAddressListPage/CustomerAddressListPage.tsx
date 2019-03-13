import Button from "@material-ui/core/Button";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import AppHeader from "../../../components/AppHeader";
import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";
import { AddressTypeEnum } from "../../../types/globalTypes";
import { CustomerAddresses_user } from "../../types/CustomerAddresses";
import CustomerAddress from "../CustomerAddress/CustomerAddress";

export interface CustomerAddressListPageProps {
  customer: CustomerAddresses_user;
  disabled: boolean;
  onAdd: () => void;
  onBack: () => void;
  onEdit: (id: string) => void;
  onRemove: (id: string) => void;
  onSetAsDefault: (id: string, type: AddressTypeEnum) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    root: {
      columnGap: theme.spacing.unit * 3 + "px",
      display: "grid",
      gridTemplateColumns: "repeat(3, 1fr)",
      rowGap: theme.spacing.unit * 3 + "px"
    }
  });

const CustomerAddressListPage = withStyles(styles, {
  name: "CustomerAddressListPage"
})(
  ({
    classes,
    customer,
    disabled,
    onAdd,
    onBack,
    onEdit,
    onRemove,
    onSetAsDefault
  }: CustomerAddressListPageProps & WithStyles<typeof styles>) => (
    <Container>
      <AppHeader onBack={onBack}>
        {i18n.t("Customer Info", {
          context: "navigation"
        })}
      </AppHeader>
      <PageHeader
        title={maybe(() =>
          i18n.t("{{ firstName }} {{ lastName }} Address Book", {
            context: "customer address book",
            firstName: customer.firstName,
            lastName: customer.lastName
          })
        )}
      >
        <Button color="secondary" variant="contained" onClick={onAdd}>
          {i18n.t("Add address", {
            context: "add customer address"
          })}
          <AddIcon />
        </Button>
      </PageHeader>
      <div className={classes.root}>
        {renderCollection(
          maybe(() => customer.addresses),
          (address, addressNumber) => (
            <CustomerAddress
              address={address}
              addressNumber={addressNumber + 1}
              disabled={disabled}
              isDefaultBillingAddress={
                maybe(() => customer.defaultBillingAddress.id) ===
                maybe(() => address.id)
              }
              isDefaultShippingAddress={
                maybe(() => customer.defaultShippingAddress.id) ===
                maybe(() => address.id)
              }
              onEdit={() => onEdit(address.id)}
              onRemove={() => onRemove(address.id)}
              onSetAsDefault={type => onSetAsDefault(address.id, type)}
              key={maybe(() => address.id, "skeleton")}
            />
          )
        )}
      </div>
    </Container>
  )
);
CustomerAddressListPage.displayName = "CustomerAddressListPage";
export default CustomerAddressListPage;
