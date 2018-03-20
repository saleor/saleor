import Card from "material-ui/Card";
import Grid from "material-ui/Grid";
import { CircularProgress } from "material-ui/Progress";
import * as React from "react";
import { Redirect } from "react-router-dom";

import ErrorMessageCard from "../../components/cards/ErrorMessageCard";
import PageHeader from "../../components/PageHeader";
import i18n from "../../i18n";
import BaseCategoryForm from "../components/BaseForm";
import { categoryShowUrl } from "../index";
import {
  categoryUpdateMutation,
  TypedCategoryUpdateMutation
} from "../mutations";
import { categoryDetailsQuery, TypedCategoryDetailsQuery } from "../queries";

interface CategoryUpdateFormProps {
  id: string;
}

export const CategoryUpdateForm: React.StatelessComponent<
  CategoryUpdateFormProps
> = ({ id }) => (
  <TypedCategoryDetailsQuery query={categoryDetailsQuery} variables={{ id }}>
    {({ data, loading, error }) => {
      if (error) {
        console.error(error.message);
        return <ErrorMessageCard message={error.message} />;
      }
      const { category } = data;

      return (
        <TypedCategoryUpdateMutation mutation={categoryUpdateMutation}>
          {(mutate, result) => {
            if (
              result &&
              !result.loading &&
              result.data.categoryUpdate.errors.length === 0
            ) {
              return (
                <Redirect
                  to={categoryShowUrl(result.data.categoryUpdate.category.id)}
                />
              );
            }
            return (
              <Card style={{ maxWidth: 750 }}>
                <PageHeader
                  cancelLink={categoryShowUrl(id)}
                  title={i18n.t("Edit category", { context: "title" })}
                />
                {loading ? (
                  <CircularProgress />
                ) : (
                  <BaseCategoryForm
                    name={category.name}
                    description={category.description}
                    handleConfirm={formData =>
                      mutate({
                        variables: {
                          ...formData,
                          id
                        }
                      })
                    }
                    confirmButtonLabel={i18n.t("Save", {
                      context: "button"
                    })}
                    errors={
                      result && !result.loading
                        ? result.data.categoryUpdate.errors
                        : []
                    }
                  />
                )}
              </Card>
            );
          }}
        </TypedCategoryUpdateMutation>
      );
    }}
  </TypedCategoryDetailsQuery>
);
