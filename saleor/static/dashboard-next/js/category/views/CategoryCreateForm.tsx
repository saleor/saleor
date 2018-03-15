import Card from "material-ui/Card";
import Grid from "material-ui/Grid";
import * as React from "react";
import { Redirect } from "react-router-dom";

import BaseCategoryForm from "../components/BaseForm";
import { categoryShowUrl } from "../index";
import {
  TypedCategoryCreateMutation,
  categoryCreateMutation
} from "../mutations";
import ErrorMessageCard from "../../components/cards/ErrorMessageCard";
import PageHeader from "../../components/PageHeader";
import i18n from "../../i18n";

type CategoryCreateFormProps = {
  parentId: string;
};

export const CategoryCreateForm: React.StatelessComponent<
  CategoryCreateFormProps
> = ({ parentId }) => (
  <TypedCategoryCreateMutation mutation={categoryCreateMutation}>
    {(mutate, result) => {
      if (
        result &&
        !result.loading &&
        result.data.categoryCreate.errors.length === 0
      ) {
        return (
          <Redirect
            to={categoryShowUrl(result.data.categoryCreate.category.id)}
            push={false}
          />
        );
      }
      return (
        <Card style={{ maxWidth: 750 }}>
          <PageHeader
            cancelLink={categoryShowUrl(parentId)}
            title={i18n.t("Add category", { context: "title" })}
          />
          <BaseCategoryForm
            confirmButtonLabel={i18n.t("Add", { context: "button" })}
            description=""
            handleConfirm={formData =>
              mutate({
                variables: {
                  ...formData,
                  parentId
                }
              })
            }
            name=""
            errors={
              result && !result.loading ? result.data.categoryCreate.errors : []
            }
          />
        </Card>
      );
    }}
  </TypedCategoryCreateMutation>
);
