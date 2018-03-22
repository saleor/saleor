import DeleteForeverIcon from "material-ui-icons/DeleteForever";
import Card from "material-ui/Card";
import Grid from "material-ui/Grid";
import IconButton from "material-ui/IconButton";
import { CircularProgress } from "material-ui/Progress";
import TextField from "material-ui/TextField";
import * as React from "react";
import { Redirect } from "react-router";

import ErrorMessageCard from "../../components/cards/ErrorMessageCard";
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
  <Card>
    <TypedPageCreateMutation mutation={pageCreateMutation}>
      {(createPage, result) => {
        if (
          result &&
          !result.loading &&
          !result.data.pageCreate.errors.length
        ) {
          if (result.error) {
            console.error(result.error);
            return;
          }
          return <Redirect to="/pages/" />;
        }
        return (
          <>
            <PageHeader
              cancelLink={"/pages/"}
              title={i18n.t("Add page", { context: "title" })}
            />
            <PageBaseForm
              errors={
                result && result.data
                  ? result.data.pageCreate.errors
                  : undefined
              }
              handleSubmit={data => createPage({ variables: { id, ...data } })}
            />
          </>
        );
      }}
    </TypedPageCreateMutation>
  </Card>
);

export default PageCreateForm;
