import * as React from "react";
import { Redirect } from "react-router";

import { pageListUrl } from "..";
import { NavigatorLink } from "../../components/Navigator";
import { PageCreateMutationVariables } from "../../gql-types";
import PageDetailsPage from "../../pages/components/PageDetailsPage";
import { pageCreateMutation, TypedPageCreateMutation } from "../mutations";

interface PageCreateFormProps {
  id: string;
}
export const PageCreateForm: React.StatelessComponent<PageCreateFormProps> = ({
  id
}) => (
  <TypedPageCreateMutation mutation={pageCreateMutation}>
    {(createPage, { called, data: createResult, error, loading }) => {
      if (called && !loading && !createResult.pageCreate.errors.length) {
        return <Redirect to={pageListUrl} push={false} />;
      }
      return (
        <NavigatorLink to={pageListUrl}>
          {handleCancel => (
            <PageDetailsPage
              loading={loading}
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
            />
          )}
        </NavigatorLink>
      );
    }}
  </TypedPageCreateMutation>
);

export default PageCreateForm;
