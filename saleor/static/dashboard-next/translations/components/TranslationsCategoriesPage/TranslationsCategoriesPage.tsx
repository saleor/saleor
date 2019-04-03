import * as React from "react";

import AppHeader from "../../../components/AppHeader";
import CardSpacer from "../../../components/CardSpacer";
import Container from "../../../components/Container";
import LanguageSwitch from "../../../components/LanguageSwitch";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { LanguageCodeEnum } from "../../../types/globalTypes";
import { CategoryTranslationFragment } from "../../types/CategoryTranslationFragment";
import { TranslationsEntitiesPageProps } from "../../types/TranslationsEntitiesPage";
import TranslationFields from "../TranslationFields";

export interface TranslationsCategoriesPageProps
  extends TranslationsEntitiesPageProps {
  category: CategoryTranslationFragment;
}

export const fieldNames = {
  descriptionJson: "description",
  name: "name",
  seoDescription: "seoDescription",
  seoTitle: "seoTitle"
};

const TranslationsCategoriesPage: React.StatelessComponent<
  TranslationsCategoriesPageProps
> = ({
  activeField,
  disabled,
  languageCode,
  languages,
  category,
  saveButtonState,
  onBack,
  onEdit,
  onLanguageChange,
  onSubmit
}) => (
  <Container>
    <AppHeader onBack={onBack}>{i18n.t("Translations")}</AppHeader>
    <PageHeader
      title={i18n.t(
        'Translation Category "{{ categoryName }}" - {{ languageCode }}',
        {
          categoryName: maybe(() => category.name, "..."),
          context: "category translation page title",
          languageCode
        }
      )}
    >
      <LanguageSwitch
        currentLanguage={LanguageCodeEnum[languageCode]}
        languages={languages}
        onLanguageChange={onLanguageChange}
      />
    </PageHeader>
    <TranslationFields
      activeField={activeField}
      disabled={disabled}
      initialState={true}
      title={i18n.t("General Information")}
      fields={[
        {
          displayName: i18n.t("Category Name"),
          name: fieldNames.name,
          translation: maybe(() =>
            category.translation ? category.translation.name : null
          ),
          type: "short" as "short",
          value: maybe(() => category.name)
        },
        {
          displayName: i18n.t("Description"),
          name: fieldNames.descriptionJson,
          translation: maybe(() =>
            category.translation ? category.translation.descriptionJson : null
          ),
          type: "rich" as "rich",
          value: maybe(() => category.descriptionJson)
        }
      ]}
      saveButtonState={saveButtonState}
      onEdit={onEdit}
      onSubmit={onSubmit}
    />
    <CardSpacer />
    <TranslationFields
      activeField={activeField}
      disabled={disabled}
      initialState={true}
      title={i18n.t("Search Engine Preview")}
      fields={[
        {
          displayName: i18n.t("Search Engine Title"),
          name: fieldNames.seoTitle,
          translation: maybe(() =>
            category.translation ? category.translation.seoTitle : null
          ),
          type: "short" as "short",
          value: maybe(() => category.seoTitle)
        },
        {
          displayName: i18n.t("Search Engine Description"),
          name: fieldNames.seoDescription,
          translation: maybe(() =>
            category.translation ? category.translation.seoDescription : null
          ),
          type: "long" as "long",
          value: maybe(() => category.seoDescription)
        }
      ]}
      saveButtonState={saveButtonState}
      onEdit={onEdit}
      onSubmit={onSubmit}
    />
  </Container>
);
TranslationsCategoriesPage.displayName = "TranslationsCategoriesPage";
export default TranslationsCategoriesPage;
