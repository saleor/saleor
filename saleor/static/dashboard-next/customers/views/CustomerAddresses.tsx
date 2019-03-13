import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";
import { Route, Switch } from "react-router-dom";

import ActionDialog from "../../components/ActionDialog";
import { WindowTitle } from "../../components/WindowTitle";
import useNavigator from "../../hooks/useNavigator";
import useNotifier from "../../hooks/useNotifier";
import useShop from "../../hooks/useShop";
import i18n from "../../i18n";
import { maybe } from "../../misc";
import CustomerAddressDialog from "../components/CustomerAddressDialog";
import CustomerAddressListPage from "../components/CustomerAddressListPage";
import {
  TypedCreateCustomerAddressMutation,
  TypedRemoveCustomerAddressMutation,
  TypedSetCustomerDefaultAddressMutation,
  TypedUpdateCustomerAddressMutation
} from "../mutations";
import { TypedCustomerAddressesQuery } from "../queries";
import { CreateCustomerAddress } from "../types/CreateCustomerAddress";
import { RemoveCustomerAddress } from "../types/RemoveCustomerAddress";
import { SetCustomerDefaultAddress } from "../types/SetCustomerDefaultAddress";
import { UpdateCustomerAddress } from "../types/UpdateCustomerAddress";
import {
  customerAddressAddPath,
  customerAddressAddUrl,
  customerAddressesUrl,
  customerAddressPath,
  customerAddressRemovePath,
  customerAddressRemoveUrl,
  customerAddressUrl,
  customerUrl
} from "../urls";

interface CustomerAddressesProps {
  id: string;
}

const CustomerAddresses: React.FC<CustomerAddressesProps> = ({ id }) => {
  const navigate = useNavigator();
  const notify = useNotifier();
  const shop = useShop();

  const closeModal = () => navigate(customerAddressesUrl(id), true);

  const handleSetAddressAsDefault = (data: SetCustomerDefaultAddress) => {
    if (data.customerSetDefaultAddress.errors.length === 0) {
      closeModal();
      notify({
        text: i18n.t("Set address as default", {
          context: "notification"
        })
      });
    }
  };

  const handleAddressCreate = (data: CreateCustomerAddress) => {
    if (data.addressCreate.errors.length === 0) {
      closeModal();
    }
  };

  const handleAddressUpdate = (data: UpdateCustomerAddress) => {
    if (data.addressUpdate.errors.length === 0) {
      closeModal();
      notify({
        text: i18n.t("Updated address", {
          context: "notification"
        })
      });
    }
  };

  const handleAddressRemove = (data: RemoveCustomerAddress) => {
    if (data.addressDelete.errors.length === 0) {
      closeModal();
      notify({
        text: i18n.t("Removed address", {
          context: "notification"
        })
      });
    }
  };

  return (
    <TypedSetCustomerDefaultAddressMutation
      onCompleted={handleSetAddressAsDefault}
    >
      {(setCustomerDefaultAddress, setCustomerDefaultAddressOpts) => (
        <TypedCreateCustomerAddressMutation onCompleted={handleAddressCreate}>
          {(createCustomerAddress, createCustomerAddressOpts) => (
            <TypedUpdateCustomerAddressMutation
              onCompleted={handleAddressUpdate}
            >
              {(updateCustomerAddress, updateCustomerAddressOpts) => (
                <TypedRemoveCustomerAddressMutation
                  onCompleted={handleAddressRemove}
                >
                  {(removeCustomerAddress, removeCustomerAddressOpts) => (
                    <TypedCustomerAddressesQuery variables={{ id }}>
                      {customerData => {
                        return (
                          <>
                            <WindowTitle
                              title={maybe(() =>
                                i18n.t("{{ firstName }} {{ lastName }}", {
                                  firstName: customerData.data.user.firstName,
                                  lastName: customerData.data.user.lastName
                                })
                              )}
                            />
                            <CustomerAddressListPage
                              customer={maybe(() => customerData.data.user)}
                              disabled={customerData.loading}
                              onAdd={() => navigate(customerAddressAddUrl(id))}
                              onBack={() => navigate(customerUrl(id))}
                              onEdit={addressId =>
                                navigate(customerAddressUrl(id, addressId))
                              }
                              onRemove={addressId =>
                                navigate(
                                  customerAddressRemoveUrl(id, addressId)
                                )
                              }
                              onSetAsDefault={(addressId, type) =>
                                setCustomerDefaultAddress({
                                  variables: { id: addressId, type }
                                })
                              }
                            />
                            <Switch>
                              <Route
                                path={customerAddressAddPath(":customerId")}
                                render={({ match }) => (
                                  <CustomerAddressDialog
                                    address={undefined}
                                    confirmButtonState={"default"}
                                    countries={maybe(
                                      () =>
                                        shop.countries.map(country => ({
                                          code: country.code,
                                          label: country.country
                                        })),
                                      []
                                    )}
                                    errors={maybe(
                                      () =>
                                        updateCustomerAddressOpts.data
                                          .addressUpdate.errors,
                                      []
                                    )}
                                    open={!!match}
                                    variant="create"
                                    onClose={closeModal}
                                    onConfirm={formData =>
                                      createCustomerAddress({
                                        variables: {
                                          input: {
                                            ...formData,
                                            country: formData.country.value,
                                            userId: id
                                          }
                                        }
                                      })
                                    }
                                  />
                                )}
                              />
                              <Route
                                path={customerAddressRemovePath(
                                  ":customerId",
                                  ":addressId"
                                )}
                                render={({ match }) => (
                                  <ActionDialog
                                    open={!!match}
                                    variant="delete"
                                    title={i18n.t("Remove Address")}
                                    confirmButtonState={"default"}
                                    onClose={closeModal}
                                    onConfirm={() =>
                                      removeCustomerAddress({
                                        variables: {
                                          id: decodeURIComponent(
                                            match.params.addressId
                                          )
                                        }
                                      })
                                    }
                                  >
                                    <DialogContentText>
                                      {i18n.t(
                                        "Are you sure you want to remove this address from users address book?"
                                      )}
                                    </DialogContentText>
                                  </ActionDialog>
                                )}
                              />
                              <Route
                                path={customerAddressPath(
                                  ":customerId",
                                  ":addressId"
                                )}
                                render={({ match }) => (
                                  <CustomerAddressDialog
                                    address={maybe(() =>
                                      customerData.data.user.addresses.find(
                                        addr =>
                                          addr.id ===
                                          decodeURIComponent(
                                            match.params.addressId
                                          )
                                      )
                                    )}
                                    confirmButtonState={"default"}
                                    countries={[]}
                                    errors={maybe(
                                      () =>
                                        updateCustomerAddressOpts.data
                                          .addressUpdate.errors,
                                      []
                                    )}
                                    open={!!match}
                                    variant="edit"
                                    onClose={closeModal}
                                    onConfirm={formData =>
                                      updateCustomerAddress({
                                        variables: {
                                          id: decodeURIComponent(
                                            match.params.addressId
                                          ),
                                          input: {
                                            ...formData,
                                            country: formData.country.value
                                          }
                                        }
                                      })
                                    }
                                  />
                                )}
                              />
                            </Switch>
                          </>
                        );
                      }}
                    </TypedCustomerAddressesQuery>
                  )}
                </TypedRemoveCustomerAddressMutation>
              )}
            </TypedUpdateCustomerAddressMutation>
          )}
        </TypedCreateCustomerAddressMutation>
      )}
    </TypedSetCustomerDefaultAddressMutation>
  );
};
export default CustomerAddresses;
