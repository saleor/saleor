import * as React from "react";
import Card from "material-ui/Card";
import DeleteForeverIcon from "material-ui-icons/DeleteForever";
import Grid from "material-ui/Grid";
import IconButton from "material-ui/IconButton";
import TextField from "material-ui/TextField";
import { CircularProgress } from "material-ui/Progress";
import { Redirect } from "react-router";

import PageHeader from "../../components/PageHeader";
import PageBaseForm from "../components/PageBaseForm";
import RichTextEditor from "../../components/RichTextEditor";
import ErrorMessageCard from "../../components/cards/ErrorMessageCard";
import i18n from "../../i18n";
import {
  TypedPageDeleteMutation,
  pageDeleteMutation,
  TypedPageCreateMutation,
  pageCreateMutation
} from "../mutations";
import { TypedPageDetailsQuery, pageDetailsQuery } from "../queries";

interface PageCreateFormProps {
  id: string;
}

export const PageCreateForm: React.StatelessComponent<PageCreateFormProps> = ({
  id
}) => (
  <Card>
    <TypedPageCreateMutation mutation={pageCreateMutation}>
      {(createPage, result) => {
        if (result) {
          if (result.error) {
            console.error(result.error);
            return;
          }
          if (result.data && result.data.pageCreate.errors) {
            console.log(result.data.pageCreate.errors);
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
              handleSubmit={data => createPage({ variables: { id, ...data } })}
            />
          </>
        );
      }}
    </TypedPageCreateMutation>
  </Card>
);

export default PageCreateForm;
