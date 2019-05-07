import { stringify as stringifyQs } from "qs";
import * as React from "react";

import useNavigator from "../../hooks/useNavigator";
import useNotifier from "../../hooks/useNotifier";
import useShop from "../../hooks/useShop";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import { LanguageCodeEnum, TranslationInput } from "../../types/globalTypes";
import TranslationsCategoriesPage, {
  fieldNames
} from "../components/TranslationsCategoriesPage";
import { TypedUpdateCategoryTranslations } from "../mutations";
import { TypedCategoryTranslationDetails } from "../queries";
import { UpdateCategoryTranslations } from "../types/UpdateCategoryTranslations";
import {
  languageEntitiesUrl,
  languageEntityUrl,
  TranslatableEntities
} from "../urls";

export interface TranslationsCategoriesQueryParams {
  activeField: string;
}
export interface TranslationsCategoriesProps {
  id: string;
  languageCode: LanguageCodeEnum;
  params: TranslationsCategoriesQueryParams;
}

const TranslationsCategories: React.FC<TranslationsCategoriesProps> = ({
  id,
  languageCode,
  params
}) => {
  const navigate = useNavigator();
  const notify = useNotifier();
  const shop = useShop();

  const onEdit = (field: string) =>
    navigate(
      "?" +
        stringifyQs({
          activeField: field
        }),
      true
    );
  const onUpdate = (data: UpdateCategoryTranslations) => {
    if (data.categoryTranslate.errors.length === 0) {
      notify({
        text: i18n.t("Translation Saved")
      });
      navigate("?", true);
    }
  };

  return (
    <TypedCategoryTranslationDetails variables={{ id, language: languageCode }}>
      {categoryTranslations => (
        <TypedUpdateCategoryTranslations onCompleted={onUpdate}>
          {(updateTranslations, updateTranslationsOpts) => {
            const handleSubmit = (field: string, data: string) => {
              const input: TranslationInput = {};
              if (field === fieldNames.descriptionJson) {
                input.descriptionJson = JSON.stringify(data);
              } else if (field === fieldNames.name) {
                input.name = data;
              } else if (field === fieldNames.seoDescription) {
                input.seoDescription = data;
              } else if (field === fieldNames.seoTitle) {
                input.seoTitle = data;
              }
              updateTranslations({
                variables: {
                  id,
                  input,
                  language: languageCode
                }
              });
            };

            const saveButtonState = getMutationState(
              updateTranslationsOpts.called,
              updateTranslationsOpts.loading,
              maybe(
                () => updateTranslationsOpts.data.categoryTranslate.errors,
                []
              )
            );

            return (
              <TranslationsCategoriesPage
                activeField={params.activeField}
                disabled={
                  categoryTranslations.loading || updateTranslationsOpts.loading
                }
                languageCode={languageCode}
                languages={maybe(() => shop.languages, [])}
                saveButtonState={saveButtonState}
                onBack={() =>
                  navigate(
                    languageEntitiesUrl(
                      languageCode,
                      TranslatableEntities.categories
                    )
                  )
                }
                onEdit={onEdit}
                onLanguageChange={lang =>
                  navigate(
                    languageEntityUrl(lang, TranslatableEntities.categories, id)
                  )
                }
                onSubmit={handleSubmit}
                category={maybe(() => categoryTranslations.data.category)}
              />
            );
          }}
        </TypedUpdateCategoryTranslations>
      )}
    </TypedCategoryTranslationDetails>
  );
};
TranslationsCategories.displayName = "TranslationsCategories";
export default TranslationsCategories;
