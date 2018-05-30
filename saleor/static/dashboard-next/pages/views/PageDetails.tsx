import DeleteIcon from "@material-ui/icons/Delete";
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
import PageDetailsPage from "../components/PageDetailsPage";
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
                            <PageDetailsPage
                              onBack={handleCancel}
                              page={loading ? undefined : detailsResult.page}
                              onSubmit={data =>
                                updatePage({
                                  variables: { id, ...data }
                                })
                              }
                              errors={
                                updateResult
                                  ? updateResult.pageUpdate.errors
                                  : []
                              }
                              title={page ? page.title : undefined}
                            />
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
