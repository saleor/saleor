import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";

import ActionDialog from "../../components/ActionDialog";
import { WindowTitle } from "../../components/WindowTitle";
import useNavigator from "../../hooks/useNavigator";
import useNotifier from "../../hooks/useNotifier";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import { orderUrl } from "../../orders/urls";
import CustomerDetailsPage from "../components/CustomerDetailsPage/CustomerDetailsPage";
import {
  TypedRemoveCustomerMutation,
  TypedUpdateCustomerMutation
} from "../mutations";
import { TypedCustomerDetailsQuery } from "../queries";
import { RemoveCustomer } from "../types/RemoveCustomer";
import { UpdateCustomer } from "../types/UpdateCustomer";
import {
  customerAddressesUrl,
  customerListUrl,
  customerUrl,
  CustomerUrlQueryParams
} from "../urls";

interface CustomerDetailsViewProps {
  id: string;
  params: CustomerUrlQueryParams;
}

export const CustomerDetailsView: React.StatelessComponent<
  CustomerDetailsViewProps
> = ({ id, params }) => {
  const navigate = useNavigator();
  const notify = useNotifier();

  const handleCustomerUpdateSuccess = (data: UpdateCustomer) => {
    if (data.customerUpdate.errors.length === 0) {
      notify({
        text: i18n.t("Customer updated", {
          context: "notification"
        })
      });
    }
  };
  const handleCustomerRemoveSuccess = (data: RemoveCustomer) => {
    if (data.customerDelete.errors.length === 0) {
      notify({
        text: i18n.t("Customer removed", {
          context: "notification"
        })
      });
      navigate(customerListUrl());
    }
  };
  return (
    <TypedRemoveCustomerMutation
      variables={{ id }}
      onCompleted={handleCustomerRemoveSuccess}
    >
      {(removeCustomer, removeCustomerOpts) => (
        <TypedUpdateCustomerMutation onCompleted={handleCustomerUpdateSuccess}>
          {(updateCustomer, updateCustomerOpts) => (
            <TypedCustomerDetailsQuery
              displayLoader
              variables={{ id }}
              require={["user"]}
            >
              {customerDetails => {
                const formTransitionState = getMutationState(
                  updateCustomerOpts.called,
                  updateCustomerOpts.loading,
                  maybe(() => updateCustomerOpts.data.customerUpdate.errors)
                );
                const removeTransitionState = getMutationState(
                  removeCustomerOpts.called,
                  removeCustomerOpts.loading,
                  maybe(() => removeCustomerOpts.data.customerDelete.errors)
                );

                return (
                  <>
                    <WindowTitle
                      title={maybe(() => customerDetails.data.user.email)}
                    />
                    <CustomerDetailsPage
                      customer={customerDetails.data.user}
                      disabled={
                        customerDetails.loading ||
                        updateCustomerOpts.loading ||
                        removeCustomerOpts.loading
                      }
                      errors={maybe(
                        () => updateCustomerOpts.data.customerUpdate.errors
                      )}
                      saveButtonBar={formTransitionState}
                      onAddressManageClick={() =>
                        navigate(customerAddressesUrl(id))
                      }
                      onBack={() => navigate(customerListUrl())}
                      onRowClick={id => navigate(orderUrl(id))}
                      onSubmit={formData =>
                        updateCustomer({
                          variables: {
                            id,
                            input: {
                              email: formData.email,
                              firstName: formData.firstName,
                              isActive: formData.isActive,
                              lastName: formData.lastName,
                              note: formData.note
                            }
                          }
                        })
                      }
                      onDelete={() =>
                        navigate(
                          customerUrl(id, {
                            action: "remove"
                          })
                        )
                      }
                      onViewAllOrdersClick={() => undefined} // TODO: add filters to order #3172
                    />
                    <ActionDialog
                      confirmButtonState={removeTransitionState}
                      onClose={() => navigate(customerUrl(id), true)}
                      onConfirm={() => removeCustomer()}
                      title={i18n.t("Remove customer", {
                        context: "modal title"
                      })}
                      variant="delete"
                      open={params.action === "remove"}
                    >
                      <DialogContentText
                        dangerouslySetInnerHTML={{
                          __html: i18n.t(
                            "Are you sure you want to remove <strong>{{ email }}</strong>?",
                            {
                              context: "modal content",
                              email: maybe(
                                () => customerDetails.data.user.email,
                                "..."
                              )
                            }
                          )
                        }}
                      />
                    </ActionDialog>
                  </>
                );
              }}
            </TypedCustomerDetailsQuery>
          )}
        </TypedUpdateCustomerMutation>
      )}
    </TypedRemoveCustomerMutation>
  );
};
export default CustomerDetailsView;
