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
  TypedPageUpdateMutation,
  pageUpdateMutation
} from "../mutations";
import { TypedPageDetailsQuery, pageDetailsQuery } from "../queries";

interface PageUpdateFormProps {
  id: string;
}

export const PageUpdateForm: React.StatelessComponent<PageUpdateFormProps> = ({
  id
}) => (
  <TypedPageDetailsQuery query={pageDetailsQuery} variables={{ id }}>
    {({ data, error, loading }) => {
      if (error) {
        return (
          <Grid container spacing={16}>
            <Grid item xs={12} md={9}>
              <ErrorMessageCard
                message={i18n.t("Unable to find matching page.")}
              />
            </Grid>
          </Grid>
        );
      }
      if (loading) {
        return <>loading</>;
      }
      const { page } = data;
      const formInitialValues = {
        title: page.title,
        slug: page.slug,
        content: page.content,
        availableOn: page.availableOn,
        isVisible: page.isVisible
      };
      return (
        <Card>
          <TypedPageDeleteMutation mutation={pageDeleteMutation}>
            {(deletePage, result) => {
              if (result) {
                if (result.error) {
                  console.error(result.error);
                  return;
                }
                if (result.data && result.data.pageDelete.errors) {
                  console.log(result.data.pageDelete.errors);
                  return;
                }
                // FIXME: component is loaded with previous state (meaning that delete  d page will still be there until table reload)
                return <Redirect to="/pages/" />;
              }
              return (
                <TypedPageUpdateMutation mutation={pageUpdateMutation}>
                  {(updatePage, result) => {
                    if (result) {
                      if (result.error) {
                        console.error(result.error);
                        return;
                      }
                      if (result.data && result.data.pageUpdate.errors) {
                        console.log(result.data.pageUpdate.errors);
                        return;
                      }
                      return <Redirect to="/pages/" />;
                    }
                    return (
                      <>
                        <PageHeader
                          cancelLink={"/pages/"}
                          title={i18n.t("Edit page", { context: "title" })}
                        >
                          <IconButton
                            onClick={() => deletePage({ variables: { id } })}
                          >
                            <DeleteForeverIcon />
                          </IconButton>
                        </PageHeader>
                        {loading ? (
                          <CircularProgress />
                        ) : (
                          <PageBaseForm
                            handleSubmit={data =>
                              updatePage({ variables: { id, ...data } })
                            }
                            formInitialValues={formInitialValues}
                            created={page.created}
                          />
                        )}
                      </>
                    );
                  }}
                </TypedPageUpdateMutation>
              );
            }}
          </TypedPageDeleteMutation>
        </Card>
      );
    }}
  </TypedPageDetailsQuery>
);

export default PageUpdateForm;
