import * as React from "react";

import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import i18n from "../../i18n";
import { maybe } from "../../misc";
import CustomerDetailsPage from "../components/CustomerDetailsPage/CustomerDetailsPage";
import { TypedUpdateCustomerMutation } from "../mutations";
import { TypedCustomerDetailsQuery } from "../queries";
import { UpdateCustomer } from "../types/UpdateCustomer";
import { customerListUrl, customerUrl } from "../urls";

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
          return (
            <TypedUpdateCustomerMutation
              onCompleted={handleCustomerUpdateSuccess}
            >
              {(updateCustomer, updateCustomerOpts) => (
                <TypedCustomerDetailsQuery variables={{ id }}>
                  {customerDetails => (
                    <CustomerDetailsPage
                      customer={customerDetails.data.user}
                      disabled={
                        customerDetails.loading || updateCustomerOpts.loading
                      }
                      errors={maybe(
                        () => updateCustomerOpts.data.customerUpdate.errors
                      )}
                      onAddressManageClick={() => undefined} // TODO: add address management #3173
                      onBack={() => navigate(customerListUrl)}
                      onRowClick={id => () =>
                        navigate(customerUrl(encodeURIComponent(id)))}
                      onSubmit={formData =>
                        updateCustomer({
                          variables: {
                            id,
                            input: {
                              email: formData.email,
                              note: formData.note // TODO: add isActive #3174
                            }
                          }
                        })
                      }
                      onDelete={() => undefined} // add removal modal #3175
                      onViewAllOrdersClick={() => undefined} // TODO: add filters to order #3172
                    />
                  )}
                </TypedCustomerDetailsQuery>
              )}
            </TypedUpdateCustomerMutation>
          );
        }}
      </Messages>
    )}
  </Navigator>
);
export default CustomerDetailsView;
