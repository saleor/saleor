import Card from "material-ui/Card";
import Grid from "material-ui/Grid";
import { CircularProgress } from "material-ui/Progress";
import * as React from "react";
import { Redirect } from "react-router-dom";

import ErrorMessageCard from "../../components/cards/ErrorMessageCard";
import { NavigatorLink } from "../../components/Navigator";
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
          {(mutate, { called, data, loading }) => {
            if (called && !loading && data.categoryUpdate.errors.length === 0) {
              return (
                <Redirect
                  to={categoryShowUrl(data.categoryUpdate.category.id)}
                />
              );
            }
            return (
              <NavigatorLink to={categoryShowUrl(id)}>
                {handleCancel => (
                  <Card style={{ maxWidth: 750 }}>
                    <PageHeader
                      onCancel={handleCancel}
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
                          called && !loading ? data.categoryUpdate.errors : []
                        }
                      />
                    )}
                  </Card>
                )}
              </NavigatorLink>
            );
          }}
        </TypedCategoryUpdateMutation>
      );
    }}
  </TypedCategoryDetailsQuery>
);
