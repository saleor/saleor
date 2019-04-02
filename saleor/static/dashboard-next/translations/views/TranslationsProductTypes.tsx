import { stringify as stringifyQs } from "qs";
import * as React from "react";

import useNavigator from "../../hooks/useNavigator";
import useNotifier from "../../hooks/useNotifier";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import {
  LanguageCodeEnum,
  NameTranslationInput
} from "../../types/globalTypes";
import TranslationsProductTypesPage, {
  fieldNames
} from "../components/TranslationsProductTypesPage";
import {
  TypedUpdateAttributeTranslations,
  TypedUpdateAttributeValueTranslations
} from "../mutations";
import { TypedProductTypeTranslationDetails } from "../queries";
import { UpdateAttributeTranslations } from "../types/UpdateAttributeTranslations";
import { UpdateAttributeValueTranslations } from "../types/UpdateAttributeValueTranslations";

export interface TranslationsProductTypesQueryParams {
  activeField: string;
}
export interface TranslationsProductTypesProps {
  id: string;
  languageCode: LanguageCodeEnum;
  params: TranslationsProductTypesQueryParams;
}

const TranslationsProductTypes: React.FC<TranslationsProductTypesProps> = ({
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
  const onAttributeUpdate = (data: UpdateAttributeTranslations) => {
    if (data.attributeTranslate.errors.length === 0) {
      notify({
        text: i18n.t("Translation Saved")
      });
      navigate("?", true);
    }
  };
  const onAttributeValueUpdate = (data: UpdateAttributeValueTranslations) => {
    if (data.attributeValueTranslate.errors.length === 0) {
      notify({
        text: i18n.t("Translation Saved")
      });
      navigate("?", true);
    }
  };

  return (
    <TypedProductTypeTranslationDetails
      variables={{ id, language: languageCode }}
    >
      {collectionTranslations => (
        <TypedUpdateAttributeTranslations onCompleted={onAttributeUpdate}>
          {(updateAttributeTranslations, updateAttributeTranslationsOpts) => (
            <TypedUpdateAttributeValueTranslations
              onCompleted={onAttributeValueUpdate}
            >
              {(
                updateAttributeValueTranslations,
                updateAttributeValueTranslationsOpts
              ) => {
                const handleSubmit = (field: string, data: string) => {
                  const input: NameTranslationInput = {};
                  const [fieldName, fieldId] = field.split(":");
                  if (fieldName === fieldNames.attribute) {
                    input.name = data;
                    updateAttributeTranslations({
                      variables: {
                        id: fieldId,
                        input,
                        language: languageCode
                      }
                    });
                  } else if (fieldName === fieldNames.value) {
                    input.name = data;
                    updateAttributeValueTranslations({
                      variables: {
                        id: fieldId,
                        input,
                        language: languageCode
                      }
                    });
                  }
                };

                const saveButtonState = getMutationState(
                  updateAttributeTranslationsOpts.called ||
                    updateAttributeTranslationsOpts.called,
                  updateAttributeTranslationsOpts.loading ||
                    updateAttributeTranslationsOpts.loading,
                  maybe(
                    () =>
                      updateAttributeTranslationsOpts.data.attributeTranslate
                        .errors,
                    []
                  ),
                  maybe(
                    () =>
                      updateAttributeValueTranslationsOpts.data
                        .attributeValueTranslate.errors,
                    []
                  )
                );

                return (
                  <TranslationsProductTypesPage
                    activeField={params.activeField}
                    disabled={
                      collectionTranslations.loading ||
                      updateAttributeTranslationsOpts.loading ||
                      updateAttributeValueTranslationsOpts.loading
                    }
                    languageCode={languageCode}
                    saveButtonState={saveButtonState}
                    onEdit={onEdit}
                    onSubmit={handleSubmit}
                    productType={maybe(
                      () => collectionTranslations.data.productType
                    )}
                  />
                );
              }}
            </TypedUpdateAttributeValueTranslations>
          )}
        </TypedUpdateAttributeTranslations>
      )}
    </TypedProductTypeTranslationDetails>
  );
};
TranslationsProductTypes.displayName = "TranslationsProductTypes";
export default TranslationsProductTypes;
