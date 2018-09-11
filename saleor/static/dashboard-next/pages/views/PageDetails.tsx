import * as React from "react";
import { Redirect } from "react-router";

import { pageListUrl } from "..";
import ErrorMessageCard from "../../components/ErrorMessageCard";
import { NavigatorLink } from "../../components/Navigator";
import i18n from "../../i18n";
import PageDetailsPage from "../components/PageDetailsPage";
import { TypedPageDeleteMutation, TypedPageUpdateMutation } from "../mutations";
import { pageDetailsQuery, TypedPageDetailsQuery } from "../queries";

interface PageUpdateFormProps {
  id: string;
}

interface PageUpdateFormState {
  opened: boolean;
}

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
              <ErrorMessageCard
                message={i18n.t("Unable to find matching page.")}
              />
            );
          }
          return (
            <TypedPageDeleteMutation>
              {(
                _,
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
                  <TypedPageUpdateMutation>
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
                        updateResult &&
                        updateResult.pageUpdate &&
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
                              title={
                                detailsResult && detailsResult.page
                                  ? detailsResult.page.title
                                  : undefined
                              }
                              disabled={
                                loading || deleteInProgress || updateInProgress
                              }
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
