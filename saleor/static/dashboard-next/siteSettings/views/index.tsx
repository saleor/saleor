import * as React from "react";

import Toggle from "../../components/Toggle";
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

export const SiteSettings: React.StatelessComponent<{}> = () => (
  <Toggle>
    {(openedAddKeyDialog, { toggle: toggleAddKeyDialog }) => {
      return (
        <TypedSiteSettingsQuery>
          {siteSettings => (
            <TypedAuthorizationKeyAdd>
              {(addAuthorizationKey, addAuthorizationKeyOpts) => (
                <TypedAuthorizationKeyDelete>
                  {(deleteAuthorizationKey, _) => (
                    <TypedShopSettingsUpdate>
                      {(updateShopSettings, updateShopSettingsOpts) => {
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
                                domain: data.domain
                              },
                              shopSettingsInput: {
                                description: data.description,
                                headerText: data.name
                              }
                            }
                          });
                        return (
                          <>
                            <SiteSettingsPage
                              disabled={loading}
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
);
export default SiteSettings;
