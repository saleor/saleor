import * as React from "react";

import AppHeader from "../../../components/AppHeader";
import CardSpacer from "../../../components/CardSpacer";
import Container from "../../../components/Container";
import LanguageSwitch from "../../../components/LanguageSwitch";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { LanguageCodeEnum } from "../../../types/globalTypes";
import { ProductTranslationFragment } from "../../types/ProductTranslationFragment";
import { TranslationsEntitiesPageProps } from "../../types/TranslationsEntitiesPage";
import TranslationFields from "../TranslationFields";

export interface TranslationsProductsPageProps
  extends TranslationsEntitiesPageProps {
  product: ProductTranslationFragment;
}

export const fieldNames = {
  descriptionJson: "description",
  name: "name",
  seoDescription: "seoDescription",
  seoTitle: "seoTitle"
};

const TranslationsProductsPage: React.StatelessComponent<
  TranslationsProductsPageProps
> = ({
  activeField,
  disabled,
  languageCode,
  languages,
  product,
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
        'Translation Product "{{ productName }}" - {{ languageCode }}',
        {
          context: "product translation page title",
          languageCode,
          productName: maybe(() => product.name, "...")
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
          displayName: i18n.t("Product Name"),
          name: fieldNames.name,
          translation: maybe(() =>
            product.translation ? product.translation.name : null
          ),
          type: "short" as "short",
          value: maybe(() => product.name)
        },
        {
          displayName: i18n.t("Description"),
          name: fieldNames.descriptionJson,
          translation: maybe(() =>
            product.translation ? product.translation.descriptionJson : null
          ),
          type: "rich" as "rich",
          value: maybe(() => product.descriptionJson)
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
            product.translation ? product.translation.seoTitle : null
          ),
          type: "short" as "short",
          value: maybe(() => product.seoTitle)
        },
        {
          displayName: i18n.t("Search Engine Description"),
          name: fieldNames.seoDescription,
          translation: maybe(() =>
            product.translation ? product.translation.seoDescription : null
          ),
          type: "long" as "long",
          value: maybe(() => product.seoDescription)
        }
      ]}
      saveButtonState={saveButtonState}
      onEdit={onEdit}
      onSubmit={onSubmit}
    />
  </Container>
);
TranslationsProductsPage.displayName = "TranslationsProductsPage";
export default TranslationsProductsPage;
