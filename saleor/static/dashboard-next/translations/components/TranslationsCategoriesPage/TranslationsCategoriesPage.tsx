import * as React from "react";

import CardSpacer from "../../../components/CardSpacer";
import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton";
import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { CategoryTranslationFragment } from "../../types/CategoryTranslationFragment";
import TranslationFields from "../TranslationFields";

export interface TranslationsCategoriesPageProps {
  activeField: string;
  disabled: boolean;
  languageCode: string;
  category: CategoryTranslationFragment;
  saveButtonState: ConfirmButtonTransitionState;
  onEdit: (field: string) => void;
  onSubmit: (field: string, data: string) => void;
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
  category,
  saveButtonState,
  onEdit,
  onSubmit
}) => (
  <Container>
    <PageHeader
      title={i18n.t(
        'Translation Category "{{ categoryName }}" - {{ languageCode }}',
        {
          categoryName: maybe(() => category.name, "..."),
          context: "category translation page title",
          languageCode
        }
      )}
    />
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
