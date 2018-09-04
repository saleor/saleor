import * as React from "react";
import { Redirect } from "react-router";

import { pageListUrl } from "..";
import { NavigatorLink } from "../../components/Navigator";
import i18n from "../../i18n";
import PageDetailsPage from "../../pages/components/PageDetailsPage";
import { TypedPageCreateMutation } from "../mutations";

export const PageCreateForm: React.StatelessComponent = () => (
  <TypedPageCreateMutation>
    {(createPage, { called, data: createResult, loading }) => {
      if (called && !loading && !createResult.pageCreate.errors.length) {
        return <Redirect to={pageListUrl} push={false} />;
      }
      return (
        <NavigatorLink to={pageListUrl}>
          {handleCancel => (
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
            />
          )}
        </NavigatorLink>
      );
    }}
  </TypedPageCreateMutation>
);

export default PageCreateForm;
