import * as React from "react";

import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import { WindowTitle } from "../../components/WindowTitle";
import i18n from "../../i18n";
import { maybe } from "../../misc";
import CustomerCreatePage from "../components/CustomerCreatePage";
import { TypedCreateCustomerMutation } from "../mutations";
import { TypedCustomerCreateDataQuery } from "../queries";
import { CreateCustomer } from "../types/CreateCustomer";
import { customerListUrl, customerUrl } from "../urls";

export const CustomerCreate: React.StatelessComponent<{}> = () => (
  <Navigator>
    {navigate => (
      <Messages>
        {pushMessage => {
          const handleCreateCustomerSuccess = (data: CreateCustomer) => {
            if (data.customerCreate.errors.length === 0) {
              pushMessage({
                text: i18n.t("Customer created", {
                  context: "notification"
                })
              });
              navigate(customerUrl(data.customerCreate.user.id));
            }
          };
          return (
            <TypedCustomerCreateDataQuery displayLoader>
              {({ data, loading }) => (
                <TypedCreateCustomerMutation
                  onCompleted={handleCreateCustomerSuccess}
                >
                  {(createCustomer, createCustomerOpts) => (
                    <>
                      <WindowTitle title={i18n.t("Create customer")} />
                      <CustomerCreatePage
                        countries={maybe(() => data.shop.countries, [])}
                        disabled={loading || createCustomerOpts.loading}
                        errors={maybe(() => {
                          const errs =
                            createCustomerOpts.data.customerCreate.errors;
                          return errs.map(err =>
                            err.field.split(":").length > 1
                              ? {
                                  ...err,
                                  field: err.field.split(":")[1]
                                }
                              : err
                          );
                        }, [])}
                        saveButtonBar={
                          createCustomerOpts.loading ? "loading" : "default"
                        }
                        onBack={() => navigate(customerListUrl())}
                        onSubmit={formData => {
                          const address = {
                            city: formData.city,
                            cityArea: formData.cityArea,
                            companyName: formData.companyName,
                            country: formData.country,
                            countryArea: formData.countryArea,
                            firstName: formData.firstName,
                            lastName: formData.lastName,
                            phone: formData.phone,
                            postalCode: formData.postalCode,
                            streetAddress1: formData.streetAddress1,
                            streetAddress2: formData.streetAddress2
                          };
                          createCustomer({
                            variables: {
                              input: {
                                defaultBillingAddress: {
                                  ...address,
                                  country: address.country.value
                                },
                                defaultShippingAddress: {
                                  ...address,
                                  country: address.country.value
                                },
                                email: formData.email,
                                firstName: formData.customerFirstName,
                                lastName: formData.customerLastName,
                                note: formData.note,
                                sendPasswordEmail: true
                              }
                            }
                          });
                        }}
                      />
                    </>
                  )}
                </TypedCreateCustomerMutation>
              )}
            </TypedCustomerCreateDataQuery>
          );
        }}
      </Messages>
    )}
  </Navigator>
);
export default CustomerCreate;
