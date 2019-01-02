import * as React from "react";
import { Redirect } from "react-router";

import { NavigatorLink } from "../../components/Navigator";
import { WindowTitle } from "../../components/WindowTitle";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import PageDetailsPage from "../../pages/components/PageDetailsPage";
import { TypedPageCreateMutation } from "../mutations";
import { pageListUrl } from "../urls";

export const PageCreateForm: React.StatelessComponent = () => (
  <TypedPageCreateMutation>
    {(createPage, { called, data: createResult, loading }) => {
      if (called && !loading && !createResult.pageCreate.errors.length) {
        return <Redirect to={pageListUrl} push={false} />;
      }
      const formTransitionState = getMutationState(
        called,
        loading,
        maybe(() => createResult.pageCreate.errors)
      );
      return (
        <NavigatorLink to={pageListUrl}>
          {handleCancel => (
            <>
              <WindowTitle title={i18n.t("Create page")} />
              <PageDetailsPage
                disabled={loading}
                page={{
                  availableOn: "",
                  content: "",
                  isVisible: false,
                  slug: "",
                  title: ""
                }}
                onBack={handleCancel}
                onSubmit={data =>
                  createPage({
                    variables: data
                  })
                }
                title={i18n.t("Add page", { context: "title" })}
                saveButtonBarState={formTransitionState}
              />
            </>
          )}
        </NavigatorLink>
      );
    }}
  </TypedPageCreateMutation>
);

export default PageCreateForm;
