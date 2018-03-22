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
  pageDeleteMutation,
  pageUpdateMutation,
  TypedPageDeleteMutation,
  TypedPageUpdateMutation
} from "../mutations";
import { pageDetailsQuery, TypedPageDetailsQuery } from "../queries";

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
        availableOn: page.availableOn,
        content: page.content,
        isVisible: page.isVisible,
        slug: page.slug,
        title: page.title
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
                  return;
                }
                // FIXME: component is loaded with previous state (meaning that delete  d page will still be there until table reload)
                return <Redirect to="/pages/" />;
              }
              return (
                <TypedPageUpdateMutation mutation={pageUpdateMutation}>
                  {(updatePage, result) => {
                    if (
                      result &&
                      !result.loading &&
                      !result.data.pageUpdate.errors
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
                            errors={
                              result && result.data
                                ? result.data.pageUpdate.errors
                                : undefined
                            }
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
