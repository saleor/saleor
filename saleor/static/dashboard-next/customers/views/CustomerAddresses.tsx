import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";
import { Route, Switch } from "react-router-dom";

import ActionDialog from "../../components/ActionDialog";
import { WindowTitle } from "../../components/WindowTitle";
import useNavigator from "../../hooks/useNavigator";
import useNotifier from "../../hooks/useNotifier";
import useShop from "../../hooks/useShop";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
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
    if (data.addressSetDefault.errors.length === 0) {
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
      {setCustomerDefaultAddress => (
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
                        const createAddressTransitionState = getMutationState(
                          createCustomerAddressOpts.called,
                          createCustomerAddressOpts.loading,
                          maybe(
                            () =>
                              createCustomerAddressOpts.data.addressCreate
                                .errors,
                            []
                          )
                        );

                        const updateAddressTransitionState = getMutationState(
                          updateCustomerAddressOpts.called,
                          updateCustomerAddressOpts.loading,
                          maybe(
                            () =>
                              updateCustomerAddressOpts.data.addressUpdate
                                .errors,
                            []
                          )
                        );

                        const removeAddressTransitionState = getMutationState(
                          removeCustomerAddressOpts.called,
                          removeCustomerAddressOpts.loading,
                          maybe(
                            () =>
                              removeCustomerAddressOpts.data.addressDelete
                                .errors,
                            []
                          )
                        );
                        return (
                          <>
                            <WindowTitle
                              title={maybe(() => customerData.data.user.email)}
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
                                  variables: { addressId, type, userId: id }
                                })
                              }
                            />
                            <Switch>
                              <Route
                                path={customerAddressAddPath(":customerId")}
                                render={({ match }) => (
                                  <CustomerAddressDialog
                                    address={undefined}
                                    confirmButtonState={
                                      createAddressTransitionState
                                    }
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
                                        createCustomerAddressOpts.data
                                          .addressCreate.errors,
                                      []
                                    )}
                                    open={!!match}
                                    variant="create"
                                    onClose={closeModal}
                                    onConfirm={formData =>
                                      createCustomerAddress({
                                        variables: {
                                          id,
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
                                    confirmButtonState={
                                      removeAddressTransitionState
                                    }
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
                                    confirmButtonState={
                                      updateAddressTransitionState
                                    }
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
