import * as React from "react";

import CardSpacer from "../../../components/CardSpacer";
import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton";
import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { CollectionTranslationFragment } from "../../types/CollectionTranslationFragment";
import TranslationFields from "../TranslationFields";

export interface TranslationsCollectionsPageProps {
  activeField: string;
  disabled: boolean;
  languageCode: string;
  collection: CollectionTranslationFragment;
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

const TranslationsCollectionsPage: React.StatelessComponent<
  TranslationsCollectionsPageProps
> = ({
  activeField,
  disabled,
  languageCode,
  collection,
  saveButtonState,
  onEdit,
  onSubmit
}) => (
  <Container>
    <PageHeader
      title={i18n.t(
        'Translation Collection "{{ collectionName }}" - {{ languageCode }}',
        {
          collectionName: maybe(() => collection.name, "..."),
          context: "collection translation page title",
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
          displayName: i18n.t("Collection Name"),
          name: fieldNames.name,
          translation: maybe(() =>
            collection.translation ? collection.translation.name : null
          ),
          type: "short" as "short",
          value: maybe(() => collection.name)
        },
        {
          displayName: i18n.t("Description"),
          name: fieldNames.descriptionJson,
          translation: maybe(() =>
            collection.translation
              ? collection.translation.descriptionJson
              : null
          ),
          type: "rich" as "rich",
          value: maybe(() => collection.descriptionJson)
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
            collection.translation ? collection.translation.seoTitle : null
          ),
          type: "short" as "short",
          value: maybe(() => collection.seoTitle)
        },
        {
          displayName: i18n.t("Search Engine Description"),
          name: fieldNames.seoDescription,
          translation: maybe(() =>
            collection.translation
              ? collection.translation.seoDescription
              : null
          ),
          type: "long" as "long",
          value: maybe(() => collection.seoDescription)
        }
      ]}
      saveButtonState={saveButtonState}
      onEdit={onEdit}
      onSubmit={onSubmit}
    />
  </Container>
);
TranslationsCollectionsPage.displayName = "TranslationsCollectionsPage";
export default TranslationsCollectionsPage;
