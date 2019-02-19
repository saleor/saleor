import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";
import { Route } from "react-router-dom";

import ActionDialog from "../../components/ActionDialog";
import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import PageDetailsPage from "../components/PageDetailsPage";
import { TypedPageRemove, TypedPageUpdate } from "../mutations";
import { TypedPageDetailsQuery } from "../queries";
import { PageRemove } from "../types/PageRemove";
import { pageListUrl, pageRemovePath, pageRemoveUrl, pageUrl } from "../urls";

export interface PageDetailsProps {
  id: string;
}

export const PageDetails: React.StatelessComponent<PageDetailsProps> = ({
  id
}) => (
  <Navigator>
    {navigate => (
      <Messages>
        {pushMessage => {
          const handlePageRemove = (data: PageRemove) => {
            if (data.pageDelete.errors.length === 0) {
              pushMessage({
                text: i18n.t("Removed page", {
                  context: "notification"
                })
              });
              navigate(pageListUrl);
            }
          };
          return (
            <TypedPageRemove variables={{ id }} onCompleted={handlePageRemove}>
              {(pageRemove, pageRemoveOpts) => (
                <TypedPageUpdate>
                  {(pageUpdate, pageUpdateOpts) => (
                    <TypedPageDetailsQuery variables={{ id }}>
                      {pageDetails => {
                        const formTransitionState = getMutationState(
                          pageUpdateOpts.called,
                          pageUpdateOpts.loading,
                          maybe(() => pageUpdateOpts.data.pageUpdate.errors)
                        );
                        const removeTransitionState = getMutationState(
                          pageRemoveOpts.called,
                          pageRemoveOpts.loading,
                          maybe(() => pageRemoveOpts.data.pageDelete.errors)
                        );

                        return (
                          <>
                            <PageDetailsPage
                              disabled={pageDetails.loading}
                              errors={maybe(
                                () => pageUpdateOpts.data.pageUpdate.errors,
                                []
                              )}
                              saveButtonBarState={formTransitionState}
                              page={pageDetails.data.page}
                              onBack={() => navigate(pageListUrl)}
                              onRemove={() => navigate(pageRemoveUrl(id))}
                              onSubmit={formData => {
                                debugger;
                                pageUpdate({
                                  variables: {
                                    id,
                                    input: {
                                      content: JSON.stringify(formData.content),
                                      isPublished: formData.isVisible
                                        ? true
                                        : formData.availableOn === "" ||
                                          formData.availableOn === null
                                        ? false
                                        : true,
                                      publicationDate: formData.isVisible
                                        ? null
                                        : formData.availableOn === ""
                                        ? null
                                        : formData.availableOn,
                                      seo: {
                                        description: formData.seoDescription,
                                        title: formData.seoTitle
                                      },
                                      slug: formData.slug,
                                      title: formData.title
                                    }
                                  }
                                });
                              }}
                            />
                            <Route
                              exact
                              path={pageRemovePath(":id")}
                              render={({ match }) => (
                                <ActionDialog
                                  open={!!match}
                                  confirmButtonState={removeTransitionState}
                                  title={i18n.t("Remove Page")}
                                  onClose={() => navigate(pageUrl(id))}
                                  onConfirm={pageRemove}
                                  variant="delete"
                                >
                                  <DialogContentText
                                    dangerouslySetInnerHTML={{
                                      __html: i18n.t(
                                        "Are you sure you want to remove <strong>{{ title }}</strong>?",
                                        {
                                          context: "page remove",
                                          title: maybe(
                                            () => pageDetails.data.page.title,
                                            "..."
                                          )
                                        }
                                      )
                                    }}
                                  />
                                </ActionDialog>
                              )}
                            />
                          </>
                        );
                      }}
                    </TypedPageDetailsQuery>
                  )}
                </TypedPageUpdate>
              )}
            </TypedPageRemove>
          );
        }}
      </Messages>
    )}
  </Navigator>
);
PageDetails.displayName = "PageDetails";
export default PageDetails;
