import DeleteForeverIcon from "material-ui-icons/DeleteForever";
import Card from "material-ui/Card";
import Grid from "material-ui/Grid";
import IconButton from "material-ui/IconButton";
import { CircularProgress } from "material-ui/Progress";
import TextField from "material-ui/TextField";
import * as React from "react";
import { Redirect } from "react-router";

import ErrorMessageCard from "../../components/cards/ErrorMessageCard";
import { NavigatorLink } from "../../components/Navigator";
import PageHeader from "../../components/PageHeader";
import RichTextEditor from "../../components/RichTextEditor";
import i18n from "../../i18n";
import PageBaseForm from "../components/PageBaseForm";
import {
  pageCreateMutation,
  pageDeleteMutation,
  TypedPageCreateMutation,
  TypedPageDeleteMutation
} from "../mutations";
import { pageDetailsQuery, TypedPageDetailsQuery } from "../queries";

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
                onCancel={handleCancel}
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
