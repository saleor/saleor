import * as React from "react";

import CardSpacer from "../../../components/CardSpacer";
import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton";
import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { PageTranslationFragment } from "../../types/PageTranslationFragment";
import TranslationFields from "../TranslationFields";

export interface TranslationsPagesPageProps {
  activeField: string;
  disabled: boolean;
  languageCode: string;
  page: PageTranslationFragment;
  saveButtonState: ConfirmButtonTransitionState;
  onEdit: (field: string) => void;
  onSubmit: (field: string, data: string) => void;
}

export const fieldNames = {
  contentJson: "content",
  seoDescription: "seoDescription",
  seoTitle: "seoTitle",
  title: "title"
};

const TranslationsPagesPage: React.StatelessComponent<
  TranslationsPagesPageProps
> = ({
  activeField,
  disabled,
  languageCode,
  page,
  saveButtonState,
  onEdit,
  onSubmit
}) => (
  <Container>
    <PageHeader
      title={i18n.t('Translation Page "{{ pageName }}" - {{ languageCode }}', {
        context: "page translation page title",
        languageCode,
        pageName: maybe(() => page.title, "...")
      })}
    />
    <TranslationFields
      activeField={activeField}
      disabled={disabled}
      initialState={true}
      title={i18n.t("General Information")}
      fields={[
        {
          displayName: i18n.t("Page Title"),
          name: fieldNames.title,
          translation: maybe(() =>
            page.translation ? page.translation.title : null
          ),
          type: "short" as "short",
          value: maybe(() => page.title)
        },
        {
          displayName: i18n.t("Content"),
          name: fieldNames.contentJson,
          translation: maybe(() =>
            page.translation ? page.translation.contentJson : null
          ),
          type: "rich" as "rich",
          value: maybe(() => page.contentJson)
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
            page.translation ? page.translation.seoTitle : null
          ),
          type: "short" as "short",
          value: maybe(() => page.seoTitle)
        },
        {
          displayName: i18n.t("Search Engine Description"),
          name: fieldNames.seoDescription,
          translation: maybe(() =>
            page.translation ? page.translation.seoDescription : null
          ),
          type: "long" as "long",
          value: maybe(() => page.seoDescription)
        }
      ]}
      saveButtonState={saveButtonState}
      onEdit={onEdit}
      onSubmit={onSubmit}
    />
  </Container>
);
TranslationsPagesPage.displayName = "TranslationsPagesPage";
export default TranslationsPagesPage;
