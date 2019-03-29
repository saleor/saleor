import { stringify as stringifyQs } from "qs";
import * as React from "react";

import useNavigator from "../../hooks/useNavigator";
import useNotifier from "../../hooks/useNotifier";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import { LanguageCodeEnum, TranslationInput } from "../../types/globalTypes";
import TranslationsCollectionsPage, {
  fieldNames
} from "../components/TranslationsCollectionsPage";
import { TypedUpdateCollectionTranslations } from "../mutations";
import { TypedCollectionTranslationDetails } from "../queries";
import { UpdateCollectionTranslations } from "../types/UpdateCollectionTranslations";

export interface TranslationsCollectionsQueryParams {
  activeField: string;
}
export interface TranslationsCollectionsProps {
  id: string;
  languageCode: LanguageCodeEnum;
  params: TranslationsCollectionsQueryParams;
}

const TranslationsCollections: React.FC<TranslationsCollectionsProps> = ({
  id,
  languageCode,
  params
}) => {
  const navigate = useNavigator();
  const notify = useNotifier();

  const onEdit = (field: string) =>
    navigate(
      "?" +
        stringifyQs({
          activeField: field
        }),
      true
    );
  const onUpdate = (data: UpdateCollectionTranslations) => {
    if (data.collectionTranslate.errors.length === 0) {
      notify({
        text: i18n.t("Translation Saved")
      });
      navigate("?", true);
    }
  };

  return (
    <TypedCollectionTranslationDetails
      variables={{ id, language: languageCode }}
    >
      {collectionTranslations => (
        <TypedUpdateCollectionTranslations onCompleted={onUpdate}>
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
                () => updateTranslationsOpts.data.collectionTranslate.errors,
                []
              )
            );

            return (
              <TranslationsCollectionsPage
                activeField={params.activeField}
                disabled={
                  collectionTranslations.loading ||
                  updateTranslationsOpts.loading
                }
                languageCode={languageCode}
                saveButtonState={saveButtonState}
                onEdit={onEdit}
                onSubmit={handleSubmit}
                collection={maybe(() => collectionTranslations.data.collection)}
              />
            );
          }}
        </TypedUpdateCollectionTranslations>
      )}
    </TypedCollectionTranslationDetails>
  );
};
TranslationsCollections.displayName = "TranslationsCollections";
export default TranslationsCollections;
