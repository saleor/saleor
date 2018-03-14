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
import Page from "../../components/Page";

type CategoryCreateFormProps = {
  parentId: string;
};

export const CategoryCreateForm: React.StatelessComponent<
  CategoryCreateFormProps
> = ({ parentId }) => (
  <Page>
    <PageHeader
      cancelLink={categoryShowUrl(parentId)}
      title={i18n.t("Add category", { context: "title" })}
    />
    <Grid xs={12} md={9}>
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
                result && !result.loading
                  ? result.data.categoryCreate.errors
                  : []
              }
            />
          );
        }}
      </TypedCategoryCreateMutation>
    </Grid>
  </Page>
);
