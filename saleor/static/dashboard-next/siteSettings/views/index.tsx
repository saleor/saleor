import * as React from "react";

import Messages from "../../components/messages";
import Toggle from "../../components/Toggle";
import i18n from "../../i18n";
import { maybe } from "../../misc";
import { AuthorizationKeyType } from "../../types/globalTypes";
import SiteSettingsKeyDialog, {
  SiteSettingsKeyDialogForm
} from "../components/SiteSettingsKeyDialog";
import SiteSettingsPage, {
  SiteSettingsPageFormData
} from "../components/SiteSettingsPage";
import {
  TypedAuthorizationKeyAdd,
  TypedAuthorizationKeyDelete,
  TypedShopSettingsUpdate
} from "../mutations";
import { TypedSiteSettingsQuery } from "../queries";
import { AuthorizationKeyAdd } from "../types/AuthorizationKeyAdd";
import { AuthorizationKeyDelete } from "../types/AuthorizationKeyDelete";
import { ShopSettingsUpdate } from "../types/ShopSettingsUpdate";

export const SiteSettings: React.StatelessComponent<{}> = () => (
  <Messages>
    {pushMessage => (
      <Toggle>
        {(openedAddKeyDialog, { toggle: toggleAddKeyDialog }) => {
          const handleAddKeySuccess = (data: AuthorizationKeyAdd) => {
            if (!maybe(() => data.authorizationKeyAdd.errors.length)) {
              pushMessage({
                text: i18n.t("Authorization key added", {
                  context: "notification"
                })
              });
              toggleAddKeyDialog();
            }
          };
          const handleDeleteKeySuccess = (data: AuthorizationKeyDelete) => {
            if (!maybe(() => data.authorizationKeyDelete.errors.length)) {
              pushMessage({
                text: i18n.t("Authorization key deleted", {
                  context: "notification"
                })
              });
            } else {
              pushMessage({
                text: i18n.t(
                  "Could not delete authorization key: {{ message }}",
                  {
                    context: "notification",
                    message: data.authorizationKeyDelete.errors[0].message
                  }
                )
              });
            }
          };
          const handleSiteSettingsSuccess = (data: ShopSettingsUpdate) => {
            if (
              !maybe(() => data.shopDomainUpdate.errors.length) &&
              !maybe(() => data.shopSettingsUpdate.errors.length)
            ) {
              pushMessage({
                text: i18n.t("Site settings updated", {
                  context: "notification"
                })
              });
            }
          };
          return (
            <TypedSiteSettingsQuery>
              {siteSettings => (
                <TypedAuthorizationKeyAdd onCompleted={handleAddKeySuccess}>
                  {(addAuthorizationKey, addAuthorizationKeyOpts) => (
                    <TypedAuthorizationKeyDelete
                      onCompleted={handleDeleteKeySuccess}
                    >
                      {(deleteAuthorizationKey, _) => (
                        <TypedShopSettingsUpdate
                          onCompleted={handleSiteSettingsSuccess}
                        >
                          {(updateShopSettings, updateShopSettingsOpts) => {
                            const errors = [
                              ...maybe(
                                () =>
                                  updateShopSettingsOpts.data.shopDomainUpdate
                                    .errors,
                                []
                              ),
                              ...maybe(
                                () =>
                                  updateShopSettingsOpts.data.shopSettingsUpdate
                                    .errors,
                                []
                              )
                            ];
                            const loading =
                              siteSettings.loading ||
                              addAuthorizationKeyOpts.loading ||
                              updateShopSettingsOpts.loading;

                            const handleAuthenticationKeyAdd = (
                              data: SiteSettingsKeyDialogForm
                            ) =>
                              addAuthorizationKey({
                                variables: {
                                  input: {
                                    key: data.key,
                                    password: data.password
                                  },
                                  keyType: data.type
                                }
                              });
                            const handleUpdateShopSettings = (
                              data: SiteSettingsPageFormData
                            ) =>
                              updateShopSettings({
                                variables: {
                                  shopDomainInput: {
                                    domain: data.domain,
                                    name: data.name,
                                  },
                                  shopSettingsInput: {
                                    description: data.description,
                                  }
                                }
                              });
                            return (
                              <>
                                <SiteSettingsPage
                                  disabled={loading}
                                  errors={errors}
                                  shop={maybe(() => siteSettings.data.shop)}
                                  onKeyAdd={toggleAddKeyDialog}
                                  onKeyRemove={keyType =>
                                    deleteAuthorizationKey({
                                      variables: { keyType }
                                    })
                                  }
                                  onSubmit={handleUpdateShopSettings}
                                />
                                <SiteSettingsKeyDialog
                                  errors={maybe(
                                    () =>
                                      addAuthorizationKeyOpts.data
                                        .authorizationKeyAdd.errors,
                                    []
                                  )}
                                  initial={{
                                    key: "",
                                    password: "",
                                    type: AuthorizationKeyType.FACEBOOK
                                  }}
                                  open={openedAddKeyDialog}
                                  onClose={toggleAddKeyDialog}
                                  onSubmit={handleAuthenticationKeyAdd}
                                />
                              </>
                            );
                          }}
                        </TypedShopSettingsUpdate>
                      )}
                    </TypedAuthorizationKeyDelete>
                  )}
                </TypedAuthorizationKeyAdd>
              )}
            </TypedSiteSettingsQuery>
          );
        }}
      </Toggle>
    )}
  </Messages>
);
export default SiteSettings;
