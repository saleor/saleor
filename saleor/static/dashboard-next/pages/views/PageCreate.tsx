import * as React from "react";

import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import { WindowTitle } from "../../components/WindowTitle";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import PageDetailsPage from "../components/PageDetailsPage";
import { TypedPageCreate } from "../mutations";
import { PageCreate as PageCreateData } from "../types/PageCreate";
import { pageListUrl, pageUrl } from "../urls";

export interface PageCreateProps {
  id: string;
}

export const PageCreate: React.StatelessComponent<PageCreateProps> = () => (
  <Messages>
    {pushMessage => (
      <Navigator>
        {navigate => {
          const handlePageCreate = (data: PageCreateData) => {
            if (data.pageCreate.errors.length === 0) {
              pushMessage({
                text: i18n.t("Successfully created new page", {
                  context: "notification"
                })
              });
              navigate(pageUrl(data.pageCreate.page.id));
            }
          };

          return (
            <TypedPageCreate onCompleted={handlePageCreate}>
              {(pageCreate, pageCreateOpts) => {
                const formTransitionState = getMutationState(
                  pageCreateOpts.called,
                  pageCreateOpts.loading,
                  maybe(() => pageCreateOpts.data.pageCreate.errors)
                );

                return (
                  <>
                    <WindowTitle title={i18n.t("Create page")} />
                    <PageDetailsPage
                      disabled={pageCreateOpts.loading}
                      errors={maybe(
                        () => pageCreateOpts.data.pageCreate.errors,
                        []
                      )}
                      saveButtonBarState={formTransitionState}
                      page={null}
                      onBack={() => navigate(pageListUrl())}
                      onRemove={() => undefined}
                      onSubmit={formData =>
                        pageCreate({
                          variables: {
                            input: {
                              contentJson: JSON.stringify(formData.content),
                              isPublished: formData.isVisible
                                ? true
                                : formData.availableOn === ""
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
                              slug: formData.slug === "" ? null : formData.slug,
                              title: formData.title
                            }
                          }
                        })
                      }
                    />
                  </>
                );
              }}
            </TypedPageCreate>
          );
        }}
      </Navigator>
    )}
  </Messages>
);
PageCreate.displayName = "PageCreate";
export default PageCreate;
