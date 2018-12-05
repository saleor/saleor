import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";
import { Route } from "react-router-dom";

import ActionDialog from "../../components/ActionDialog";
import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import { WindowTitle } from "../../components/WindowTitle";
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
  customerListUrl,
  customerRemovePath,
  customerRemoveUrl,
  customerUrl
} from "../urls";

interface CustomerDetailsViewProps {
  id: string;
}

export const CustomerDetailsView: React.StatelessComponent<
  CustomerDetailsViewProps
> = ({ id }) => (
  <Navigator>
    {navigate => (
      <Messages>
        {pushMessage => {
          const handleCustomerUpdateSuccess = (data: UpdateCustomer) => {
            if (
              data.customerUpdate.errors === null ||
              data.customerUpdate.errors.length === 0
            ) {
              pushMessage({
                text: i18n.t("Customer updated", {
                  context: "notification"
                })
              });
            }
          };
          const handleCustomerRemoveSuccess = (data: RemoveCustomer) => {
            if (
              data.customerDelete.errors === null ||
              data.customerDelete.errors.length === 0
            ) {
              pushMessage({
                text: i18n.t("Customer removed", {
                  context: "notification"
                })
              });
              navigate(customerListUrl);
            }
          };
          return (
            <TypedRemoveCustomerMutation
              variables={{ id }}
              onCompleted={handleCustomerRemoveSuccess}
            >
              {(removeCustomer, removeCustomerOpts) => (
                <TypedUpdateCustomerMutation
                  onCompleted={handleCustomerUpdateSuccess}
                >
                  {(updateCustomer, updateCustomerOpts) => (
                    <TypedCustomerDetailsQuery displayLoader variables={{ id }}>
                      {customerDetails => {
                        const formTransitionState = getMutationState(
                          updateCustomerOpts.called,
                          updateCustomerOpts.loading,
                          maybe(
                            () => updateCustomerOpts.data.customerUpdate.errors
                          )
                        );
                        const removeTransitionState = getMutationState(
                          removeCustomerOpts.called,
                          removeCustomerOpts.loading,
                          maybe(
                            () => removeCustomerOpts.data.customerDelete.errors
                          )
                        );

                        return (
                          <>
                            <WindowTitle
                              title={maybe(
                                () => customerDetails.data.user.email
                              )}
                            />
                            <CustomerDetailsPage
                              customer={customerDetails.data.user}
                              disabled={
                                customerDetails.loading ||
                                updateCustomerOpts.loading ||
                                removeCustomerOpts.loading
                              }
                              errors={maybe(
                                () =>
                                  updateCustomerOpts.data.customerUpdate.errors
                              )}
                              saveButtonBar={formTransitionState}
                              onAddressManageClick={() => undefined} // TODO: add address management #3173
                              onBack={() => navigate(customerListUrl)}
                              onRowClick={id => navigate(orderUrl(id))}
                              onSubmit={formData =>
                                updateCustomer({
                                  variables: {
                                    id,
                                    input: {
                                      email: formData.email,
                                      isActive: formData.isActive,
                                      note: formData.note
                                    }
                                  }
                                })
                              }
                              onDelete={() => navigate(customerRemoveUrl(id))}
                              onViewAllOrdersClick={() => undefined} // TODO: add filters to order #3172
                            />
                            <Route exact path={customerRemovePath(":id")}>
                              {({ match }) => (
                                <ActionDialog
                                  confirmButtonState={removeTransitionState}
                                  onClose={() => navigate(customerUrl(id))}
                                  onConfirm={() => removeCustomer()}
                                  title={i18n.t("Remove customer", {
                                    context: "modal title"
                                  })}
                                  variant="delete"
                                  open={!!match}
                                >
                                  <DialogContentText
                                    dangerouslySetInnerHTML={{
                                      __html: i18n.t(
                                        "Are you sure you want to remove <strong>{{ email }}</strong>?",
                                        {
                                          context: "modal content",
                                          email: maybe(
                                            () =>
                                              customerDetails.data.user.email
                                          )
                                        }
                                      )
                                    }}
                                  />
                                </ActionDialog>
                              )}
                            </Route>
                          </>
                        );
                      }}
                    </TypedCustomerDetailsQuery>
                  )}
                </TypedUpdateCustomerMutation>
              )}
            </TypedRemoveCustomerMutation>
          );
        }}
      </Messages>
    )}
  </Navigator>
);
export default CustomerDetailsView;
