import Card from "material-ui/Card";
import * as React from "react";
import { Redirect } from "react-router";

import { NavigatorLink } from "../../components/Navigator";
import PageHeader from "../../components/PageHeader";
import i18n from "../../i18n";
import PageBaseForm from "../components/PageBaseForm";
import { pageCreateMutation, TypedPageCreateMutation } from "../mutations";

interface PageCreateFormProps {
  id: string;
}

export const PageCreateForm: React.StatelessComponent<PageCreateFormProps> = ({
  id
}) => (
  <TypedPageCreateMutation mutation={pageCreateMutation}>
    {(createPage, { called, data, error, loading }) => {
      if (called && !loading && !data.pageCreate.errors.length) {
        if (error) {
          console.error(error);
          return;
        }
        return <Redirect to="/pages/" />;
      }
      return (
        <NavigatorLink to={"/pages/"}>
          {handleCancel => (
            <Card>
              <PageHeader
                onBack={handleCancel}
                title={i18n.t("Add page", { context: "title" })}
              />
              <PageBaseForm
                errors={called && data ? data.pageCreate.errors : undefined}
                handleSubmit={data =>
                  createPage({ variables: { id, ...data } })
                }
              />
            </Card>
          )}
        </NavigatorLink>
      );
    }}
  </TypedPageCreateMutation>
);

export default PageCreateForm;
