import * as React from "react";

import { WindowTitle } from "../../components/WindowTitle";
import { configurationMenuUrl } from "../../configuration";
import useNavigator from "../../hooks/useNavigator";
import useNotifier from "../../hooks/useNotifier";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
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
import { siteSettingsUrl, SiteSettingsUrlQueryParams } from "../urls";

export interface SiteSettingsProps {
  params: SiteSettingsUrlQueryParams;
}

export const SiteSettings: React.StatelessComponent<SiteSettingsProps> = ({
  params
}) => {
  const navigate = useNavigator();
  const notify = useNotifier();

  const handleAddKeySuccess = (data: AuthorizationKeyAdd) => {
    if (!maybe(() => data.authorizationKeyAdd.errors.length)) {
      notify({
        text: i18n.t("Authorization key added", {
          context: "notification"
        })
      });
      navigate(siteSettingsUrl());
    }
  };
  const handleDeleteKeySuccess = (data: AuthorizationKeyDelete) => {
    if (!maybe(() => data.authorizationKeyDelete.errors.length)) {
      notify({
        text: i18n.t("Authorization key deleted", {
          context: "notification"
        })
      });
    } else {
      notify({
        text: i18n.t("Could not delete authorization key: {{ message }}", {
          context: "notification",
          message: data.authorizationKeyDelete.errors[0].message
        })
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
      notify({
        text: i18n.t("Site settings updated", {
          context: "notification"
        })
      });
    }
  };
  return (
    <TypedSiteSettingsQuery displayLoader>
      {siteSettings => (
        <TypedAuthorizationKeyAdd onCompleted={handleAddKeySuccess}>
          {(addAuthorizationKey, addAuthorizationKeyOpts) => (
            <TypedAuthorizationKeyDelete onCompleted={handleDeleteKeySuccess}>
              {(deleteAuthorizationKey, _) => (
                <TypedShopSettingsUpdate
                  onCompleted={handleSiteSettingsSuccess}
                >
                  {(updateShopSettings, updateShopSettingsOpts) => {
                    const errors = [
                      ...maybe(
                        () =>
                          updateShopSettingsOpts.data.shopDomainUpdate.errors,
                        []
                      ),
                      ...maybe(
                        () =>
                          updateShopSettingsOpts.data.shopSettingsUpdate.errors,
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

                    const formTransitionState = getMutationState(
                      updateShopSettingsOpts.called,
                      updateShopSettingsOpts.loading,
                      [
                        ...maybe(
                          () =>
                            updateShopSettingsOpts.data.shopDomainUpdate.errors,
                          []
                        ),
                        ...maybe(
                          () =>
                            updateShopSettingsOpts.data.shopSettingsUpdate
                              .errors,
                          []
                        )
                      ]
                    );

                    return (
                      <>
                        <WindowTitle title={i18n.t("Site settings")} />
                        <SiteSettingsPage
                          disabled={loading}
                          errors={errors}
                          shop={maybe(() => siteSettings.data.shop)}
                          onBack={() => navigate(configurationMenuUrl)}
                          onKeyAdd={() =>
                            navigate(
                              siteSettingsUrl({
                                action: "add-key"
                              })
                            )
                          }
                          onKeyRemove={keyType =>
                            deleteAuthorizationKey({
                              variables: { keyType }
                            })
                          }
                          onSubmit={handleUpdateShopSettings}
                          saveButtonBarState={formTransitionState}
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
                          open={params.action === "add-key"}
                          onClose={() => navigate(siteSettingsUrl())}
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
};
export default SiteSettings;
