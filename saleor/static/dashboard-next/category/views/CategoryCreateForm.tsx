import Card from "material-ui/Card";
import * as React from "react";
import { Redirect } from "react-router-dom";

import Form, { FormActions, FormProps } from "../../components/Form";
import { NavigatorLink } from "../../components/Navigator";
import PageHeader from "../../components/PageHeader";
import { CategoryCreateMutationVariables } from "../../gql-types";
import i18n from "../../i18n";
import CategoryBaseForm from "../components/CategoryBaseForm";
import { categoryShowUrl } from "../index";
import {
  categoryCreateMutation,
  TypedCategoryCreateMutation
} from "../mutations";

const CategoryForm: React.ComponentType<
  FormProps<CategoryCreateMutationVariables>
> = Form;

interface CategoryCreateFormProps {
  parentId: string;
}

export const CategoryCreateForm: React.StatelessComponent<
  CategoryCreateFormProps
> = ({ parentId }) => (
  <TypedCategoryCreateMutation mutation={categoryCreateMutation}>
    {(mutate, { called, data: createResult, loading: createInProgress }) => {
      if (
        called &&
        !createInProgress &&
        createResult.categoryCreate.errors.length === 0
      ) {
        return (
          <Redirect
            to={categoryShowUrl(createResult.categoryCreate.category.id)}
            push={false}
          />
        );
      }
      const errors =
        called && !createInProgress ? createResult.categoryCreate.errors : [];
      return (
        <NavigatorLink to={categoryShowUrl(parentId)}>
          {handleCancel => (
            <CategoryForm
              initial={{
                description: "",
                name: "",
                parentId
              }}
              onSubmit={data =>
                mutate({
                  variables: data
                })
              }
            >
              {({ change, data, submit: handleSubmit }) => (
                <Card style={{ maxWidth: 750 }}>
                  <PageHeader
                    onBack={handleCancel}
                    title={i18n.t("Add category", { context: "title" })}
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
          )}
        </NavigatorLink>
      );
    }}
  </TypedCategoryCreateMutation>
);
