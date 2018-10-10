import * as React from "react";

import Toggle from "../../components/Toggle";
import { maybe } from "../../misc";
import { AuthorizationKeyType } from "../../types/globalTypes";
import SiteSettingsKeyDialog, {
  SiteSettingsKeyDialogForm
} from "../components/SiteSettingsKeyDialog";
import SiteSettingsPage, {SiteSettingsPageFormData} from "../components/SiteSettingsPage";
import {
  TypedAuthorizationKeyAdd,
  TypedShopSettingsUpdate
} from "../mutations";
import { TypedSiteSettingsQuery } from "../queries";

export const SiteSettings: React.StatelessComponent<{}> = () => (
  <TypedSiteSettingsQuery>
    {siteSettings => (
      <TypedAuthorizationKeyAdd>
        {(addAuthorizationKey, addAuthorizationKeyOpts) => (
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
              const handleUpdateShopSettings = (data: SiteSettingsPageFormData) => updateShopSettings({
                variables: {
                  shopDomainInput: {
                    domain: data.domain
                  },
                  shopSettingsInput: {
                    description: data.description,
                    headerText: data.name
                  }
                }
              })
              return (
                <Toggle>
                  {(openedAddKeyDialog, { toggle: toggleAddKeyDialog }) => (
                    <>
                      <SiteSettingsPage
                        disabled={loading}
                        shop={maybe(() => siteSettings.data.shop)}
                        onKeyAdd={toggleAddKeyDialog}
                        onKeyRemove={() => undefined}
                        onSubmit={handleUpdateShopSettings}
                      />
                      <SiteSettingsKeyDialog
                        errors={maybe(
                          () =>
                            addAuthorizationKeyOpts.data.authorizationKeyAdd
                              .errors,
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
                  )}
                </Toggle>
              );
            }}
          </TypedShopSettingsUpdate>
        )}
      </TypedAuthorizationKeyAdd>
    )}
  </TypedSiteSettingsQuery>
);
export default SiteSettings;
