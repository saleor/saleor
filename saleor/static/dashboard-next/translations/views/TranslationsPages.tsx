import { stringify as stringifyQs } from "qs";
import * as React from "react";

import useNavigator from "../../hooks/useNavigator";
import useNotifier from "../../hooks/useNotifier";
import useShop from "../../hooks/useShop";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import {
  LanguageCodeEnum,
  PageTranslationInput
} from "../../types/globalTypes";
import TranslationsPagesPage, {
  fieldNames
} from "../components/TranslationsPagesPage";
import { TypedUpdatePageTranslations } from "../mutations";
import { TypedPageTranslationDetails } from "../queries";
import { UpdatePageTranslations } from "../types/UpdatePageTranslations";
import {
  languageEntitiesUrl,
  languageEntityUrl,
  TranslatableEntities
} from "../urls";

export interface TranslationsPagesQueryParams {
  activeField: string;
}
export interface TranslationsPagesProps {
  id: string;
  languageCode: LanguageCodeEnum;
  params: TranslationsPagesQueryParams;
}

const TranslationsPages: React.FC<TranslationsPagesProps> = ({
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
  const onUpdate = (data: UpdatePageTranslations) => {
    if (data.pageTranslate.errors.length === 0) {
      notify({
        text: i18n.t("Translation Saved")
      });
      navigate("?", true);
    }
  };

  return (
    <TypedPageTranslationDetails variables={{ id, language: languageCode }}>
      {pageTranslations => (
        <TypedUpdatePageTranslations onCompleted={onUpdate}>
          {(updateTranslations, updateTranslationsOpts) => {
            const handleSubmit = (field: string, data: string) => {
              const input: PageTranslationInput = {};
              if (field === fieldNames.contentJson) {
                input.contentJson = JSON.stringify(data);
              } else if (field === fieldNames.title) {
                input.title = data;
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
              maybe(() => updateTranslationsOpts.data.pageTranslate.errors, [])
            );

            return (
              <TranslationsPagesPage
                activeField={params.activeField}
                disabled={
                  pageTranslations.loading || updateTranslationsOpts.loading
                }
                languageCode={languageCode}
                languages={maybe(() => shop.languages, [])}
                saveButtonState={saveButtonState}
                onBack={() =>
                  navigate(
                    languageEntitiesUrl(
                      languageCode,
                      TranslatableEntities.pages
                    )
                  )
                }
                onEdit={onEdit}
                onLanguageChange={lang =>
                  navigate(
                    languageEntityUrl(lang, TranslatableEntities.pages, id)
                  )
                }
                onSubmit={handleSubmit}
                page={maybe(() => pageTranslations.data.page)}
              />
            );
          }}
        </TypedUpdatePageTranslations>
      )}
    </TypedPageTranslationDetails>
  );
};
TranslationsPages.displayName = "TranslationsPages";
export default TranslationsPages;
