import Card from "material-ui/Card";
import { CircularProgress } from "material-ui/Progress";
import { withStyles } from "material-ui/styles";
import * as React from "react";
import { Redirect } from "react-router-dom";

import ErrorMessageCard from "../../components/ErrorMessageCard";
import Form, { FormActions, FormProps } from "../../components/Form";
import { NavigatorLink } from "../../components/Navigator";
import PageHeader from "../../components/PageHeader";
import { CategoryUpdateMutationVariables } from "../../gql-types";
import i18n from "../../i18n";
import CategoryBaseForm from "../components/CategoryBaseForm";
import { categoryShowUrl } from "../index";
import {
  categoryUpdateMutation,
  TypedCategoryUpdateMutation
} from "../mutations";
import { categoryDetailsQuery, TypedCategoryDetailsQuery } from "../queries";

const CategoryForm: React.ComponentType<
  FormProps<CategoryUpdateMutationVariables>
> = Form;

const decorate = withStyles(theme => ({
  root: {
    marginBottom: theme.spacing.unit * 2,
    [theme.breakpoints.up("sm")]: {
      marginLeft: "auto",
      marginRight: "auto",
      maxWidth: theme.breakpoints.width("sm")
    }
  }
}));

interface CategoryUpdateFormProps {
  id: string;
}

export const CategoryUpdateForm = decorate<CategoryUpdateFormProps>(
  ({ classes, id }) => (
    <TypedCategoryDetailsQuery query={categoryDetailsQuery} variables={{ id }}>
      {({ data, loading, error }) => {
        if (error) {
          console.error(error.message);
          return <ErrorMessageCard message={error.message} />;
        }
        const { category } = data;

        return (
          <TypedCategoryUpdateMutation mutation={categoryUpdateMutation}>
            {(
              mutate,
              { called, data: updateResult, loading: updateInProgress }
            ) => {
              if (
                called &&
                !updateInProgress &&
                updateResult.categoryUpdate.errors.length === 0
              ) {
                return (
                  <Redirect
                    to={categoryShowUrl(
                      updateResult.categoryUpdate.category.id
                    )}
                  />
                );
              }
              const errors =
                called && !updateInProgress
                  ? updateResult.categoryUpdate.errors
                  : [];
              return (
                <NavigatorLink to={categoryShowUrl(id)}>
                  {handleCancel =>
                    loading ? (
                      <CircularProgress />
                    ) : (
                      <CategoryForm
                        initial={{
                          description: category.description,
                          id: category.id,
                          name: category.name
                        }}
                        onSubmit={data =>
                          mutate({
                            variables: data
                          })
                        }
                      >
                        {({ change, data, submit: handleSubmit }) => (
                          <Card className={classes.root}>
                            <PageHeader
                              onBack={handleCancel}
                              title={i18n.t("Category details", {
                                context: "title"
                              })}
                            />
                            <CategoryBaseForm
                              description={data.description}
                              errors={errors}
                              name={data.name}
                              onChange={change}
                            />
                            <FormActions
                              onCancel={handleCancel}
                              onSubmit={handleSubmit}
                              submitLabel={i18n.t("Save", {
                                context: "button"
                              })}
                            />
                          </Card>
                        )}
                      </CategoryForm>
                    )
                  }
                </NavigatorLink>
              );
            }}
          </TypedCategoryUpdateMutation>
        );
      }}
    </TypedCategoryDetailsQuery>
  )
);
