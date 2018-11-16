import * as React from "react";
import { Route } from "react-router-dom";

import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import { WindowTitle } from "../../components/WindowTitle";
import { configurationMenuUrl } from "../../configuration";
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
import { siteSettingsAddKeyUrl, siteSettingsUrl } from "../urls";

export const SiteSettings: React.StatelessComponent<{}> = () => (
  <Navigator>
    {navigate => (
      <Messages>
        {pushMessage => {
          const handleAddKeySuccess = (data: AuthorizationKeyAdd) => {
            if (!maybe(() => data.authorizationKeyAdd.errors.length)) {
              pushMessage({
                text: i18n.t("Authorization key added", {
                  context: "notification"
                })
              });
              navigate(siteSettingsUrl);
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
              (!data.shopDomainUpdate.errors ||
                data.shopDomainUpdate.errors.length === 0) &&
              (!data.shopSettingsUpdate.errors ||
                data.shopSettingsUpdate.errors.length === 0)
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
                                    name: data.name
                                  },
                                  shopSettingsInput: {
                                    description: data.description
                                  }
                                }
                              });
                            return (
                              <>
                                <WindowTitle title={i18n.t("Site settings")} />
                                <SiteSettingsPage
                                  disabled={loading}
                                  errors={errors}
                                  shop={maybe(() => siteSettings.data.shop)}
                                  onBack={() => navigate(configurationMenuUrl)}
                                  onKeyAdd={() =>
                                    navigate(siteSettingsAddKeyUrl)
                                  }
                                  onKeyRemove={keyType =>
                                    deleteAuthorizationKey({
                                      variables: { keyType }
                                    })
                                  }
                                  onSubmit={handleUpdateShopSettings}
                                />
                                <Route
                                  path={siteSettingsAddKeyUrl}
                                  render={({ match }) => (
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
                                      open={!!match}
                                      onClose={() => navigate(siteSettingsUrl)}
                                      onSubmit={handleAuthenticationKeyAdd}
                                    />
                                  )}
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
      </Messages>
    )}
  </Navigator>
);
export default SiteSettings;
