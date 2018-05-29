import Card from "material-ui/Card";
import * as React from "react";
import { Redirect } from "react-router";

import { pageListUrl } from "..";
import Form, { FormActions, FormProps } from "../../components/Form";
import { NavigatorLink } from "../../components/Navigator";
import PageHeader from "../../components/PageHeader";
import { PageCreateMutationVariables } from "../../gql-types";
import i18n from "../../i18n";
import PageBaseForm from "../components/PageBaseForm";
import { pageCreateMutation, TypedPageCreateMutation } from "../mutations";

const PageForm: React.ComponentType<
  FormProps<PageCreateMutationVariables>
> = Form;

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
            <PageForm
              initial={{
                availableOn: "",
                content: "",
                isVisible: false,
                slug: "",
                title: ""
              }}
              onSubmit={data =>
                createPage({
                  variables: data
                })
              }
            >
              {({ change, data, submit: handleSubmit }) => (
                <Card>
                  <PageHeader
                    onBack={handleCancel}
                    title={i18n.t("Add page", { context: "title" })}
                  />
                  <PageBaseForm
                    errors={
                      called && createResult
                        ? createResult.pageCreate.errors
                        : []
                    }
                    title={data.title}
                    content={data.content}
                    slug={data.slug}
                    availableOn={data.availableOn}
                    isVisible={data.isVisible}
                    onChange={change}
                  />
                  <FormActions
                    onCancel={handleCancel}
                    onSubmit={handleSubmit}
                    submitLabel={i18n.t("Save", {
                      context: "button"
                    })}
                  />
                </Card>
              )}
            </PageForm>
          )}
        </NavigatorLink>
      );
    }}
  </TypedPageCreateMutation>
);

export default PageCreateForm;
