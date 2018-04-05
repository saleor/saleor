import DeleteIcon from "material-ui-icons/Delete";
import Card from "material-ui/Card";
import { DialogContentText } from "material-ui/Dialog";
import Grid from "material-ui/Grid";
import IconButton from "material-ui/IconButton";
import { CircularProgress } from "material-ui/Progress";
import * as React from "react";
import { Redirect } from "react-router";

import { pageListUrl } from "..";
import ErrorMessageCard from "../../components/ErrorMessageCard";
import Form, { FormActions, FormProps } from "../../components/Form";
import { NavigatorLink } from "../../components/Navigator";
import PageHeader from "../../components/PageHeader";
import { PageUpdateMutationVariables } from "../../gql-types";
import i18n from "../../i18n";
import PageBaseForm from "../components/PageBaseForm";
import PageDeleteDialog from "../components/PageDeleteDialog";
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

interface PageUpdateFormState {
  opened: boolean;
}

const PageForm: React.ComponentType<
  FormProps<PageUpdateMutationVariables>
> = Form;

export class PageUpdateForm extends React.Component<
  PageUpdateFormProps,
  PageUpdateFormState
> {
  state = { opened: false };

  handleRemoveButtonClick = () => {
    this.setState(prevState => ({ opened: !prevState.opened }));
  };

  render() {
    const { id } = this.props;
    return (
      <TypedPageDetailsQuery query={pageDetailsQuery} variables={{ id }}>
        {({ data: detailsResult, error, loading }) => {
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
            return <CircularProgress />;
          }
          const { page } = detailsResult;
          const formInitialValues = {
            availableOn: page.availableOn,
            content: page.content,
            isVisible: page.isVisible,
            slug: page.slug,
            title: page.title
          };
          return (
            <TypedPageDeleteMutation mutation={pageDeleteMutation}>
              {(
                deletePage,
                { called, data: deleteResult, error, loading: deleteInProgress }
              ) => {
                if (called && !deleteInProgress) {
                  if (error) {
                    console.error(error);
                    return;
                  }
                  if (
                    deleteResult.pageDelete.errors &&
                    deleteResult.pageDelete.errors.length
                  ) {
                    console.error(deleteResult.pageDelete);
                    return;
                  }
                  // FIXME: component is loaded with previous state (meaning that deleted page will still be there until table reload)
                  this.handleRemoveButtonClick();
                  return <Redirect to={pageListUrl} />;
                }
                return (
                  <TypedPageUpdateMutation mutation={pageUpdateMutation}>
                    {(
                      updatePage,
                      {
                        called,
                        data: updateResult,
                        error,
                        loading: updateInProgress
                      }
                    ) => {
                      if (
                        called &&
                        !updateInProgress &&
                        !updateResult.pageUpdate.errors.length
                      ) {
                        if (error) {
                          console.error(error);
                          return;
                        }
                        return <Redirect to={pageListUrl} />;
                      }
                      return (
                        <NavigatorLink to={pageListUrl}>
                          {handleCancel => (
                            <>
                              <Card>
                                <PageForm
                                  initial={{
                                    availableOn: page.availableOn || "",
                                    content: page.content || "",
                                    id,
                                    isVisible: page.isVisible,
                                    slug: page.slug || "",
                                    title: page.title || ""
                                  }}
                                  onSubmit={data =>
                                    updatePage({
                                      variables: data
                                    })
                                  }
                                >
                                  {({ change, data, submit: handleSubmit }) => (
                                    <>
                                      <PageHeader
                                        onBack={handleCancel}
                                        title={i18n.t("Page details", {
                                          context: "title"
                                        })}
                                      >
                                        <IconButton
                                          onClick={this.handleRemoveButtonClick}
                                        >
                                          <DeleteIcon />
                                        </IconButton>
                                      </PageHeader>
                                      <PageBaseForm
                                        onChange={change}
                                        created={page.created}
                                        errors={
                                          updateResult
                                            ? updateResult.pageUpdate.errors
                                            : []
                                        }
                                        title={data.title}
                                        content={data.content}
                                        slug={data.slug}
                                        availableOn={data.availableOn}
                                        isVisible={data.isVisible}
                                      />
                                      <FormActions
                                        onCancel={handleCancel}
                                        onSubmit={handleSubmit}
                                        submitLabel={i18n.t("Save", {
                                          context: "button"
                                        })}
                                      />
                                    </>
                                  )}
                                </PageForm>
                              </Card>
                              {!loading && (
                                <PageDeleteDialog
                                  onClose={this.handleRemoveButtonClick}
                                  onConfirm={() =>
                                    deletePage({ variables: { id } })
                                  }
                                  opened={this.state.opened}
                                >
                                  <DialogContentText
                                    dangerouslySetInnerHTML={{
                                      __html: i18n.t(
                                        "Are you sure you want to remove <strong>{{name}}</strong>?",
                                        { name: page.title }
                                      )
                                    }}
                                  />
                                </PageDeleteDialog>
                              )}
                            </>
                          )}
                        </NavigatorLink>
                      );
                    }}
                  </TypedPageUpdateMutation>
                );
              }}
            </TypedPageDeleteMutation>
          );
        }}
      </TypedPageDetailsQuery>
    );
  }
}

export default PageUpdateForm;
