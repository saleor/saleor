import * as React from "react";
import Card from "material-ui/Card";
import Grid from "material-ui/Grid";
import TextField from "material-ui/TextField";
import { CircularProgress } from "material-ui/Progress";
import { Redirect } from "react-router";

import PageHeader from "../../components/PageHeader";
import PageUpdateFormComponent from "../components/PageUpdateFormComponent";
import RichTextEditor from "../../components/RichTextEditor";
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
    {({ data: { page }, error, loading }) => {
      if (error) {
        return;
      }
      if (loading) {
        return <>loading</>;
      }
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
                return <Redirect to="/pages/" />; // FIXME component is loaded with previous state (meaning that deleted page will still be there until table reload)
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
                          handleDelete={() => deletePage({ variables: { id } })}
                          title={i18n.t("Edit page", { context: "title" })}
                        />
                        {loading ? (
                          <CircularProgress />
                        ) : (
                          <PageUpdateFormComponent
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
