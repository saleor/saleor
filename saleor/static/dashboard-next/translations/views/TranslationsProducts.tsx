import { stringify as stringifyQs } from "qs";
import * as React from "react";

import useNavigator from "../../hooks/useNavigator";
import useNotifier from "../../hooks/useNotifier";
import useShop from "../../hooks/useShop";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import { LanguageCodeEnum, TranslationInput } from "../../types/globalTypes";
import TranslationsProductsPage, {
  fieldNames
} from "../components/TranslationsProductsPage";
import { TypedUpdateProductTranslations } from "../mutations";
import { TypedProductTranslationDetails } from "../queries";
import { UpdateProductTranslations } from "../types/UpdateProductTranslations";
import {
  languageEntitiesUrl,
  languageEntityUrl,
  TranslatableEntities
} from "../urls";

export interface TranslationsProductsQueryParams {
  activeField: string;
}
export interface TranslationsProductsProps {
  id: string;
  languageCode: LanguageCodeEnum;
  params: TranslationsProductsQueryParams;
}

const TranslationsProducts: React.FC<TranslationsProductsProps> = ({
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
  const onUpdate = (data: UpdateProductTranslations) => {
    if (data.productTranslate.errors.length === 0) {
      notify({
        text: i18n.t("Translation Saved")
      });
      navigate("?", true);
    }
  };

  return (
    <TypedProductTranslationDetails variables={{ id, language: languageCode }}>
      {productTranslations => (
        <TypedUpdateProductTranslations onCompleted={onUpdate}>
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
                () => updateTranslationsOpts.data.productTranslate.errors,
                []
              )
            );

            return (
              <TranslationsProductsPage
                activeField={params.activeField}
                disabled={
                  productTranslations.loading || updateTranslationsOpts.loading
                }
                languageCode={languageCode}
                languages={maybe(() => shop.languages, [])}
                saveButtonState={saveButtonState}
                onBack={() =>
                  navigate(
                    languageEntitiesUrl(
                      languageCode,
                      TranslatableEntities.products
                    )
                  )
                }
                onEdit={onEdit}
                onLanguageChange={lang =>
                  navigate(
                    languageEntityUrl(lang, TranslatableEntities.products, id)
                  )
                }
                onSubmit={handleSubmit}
                product={maybe(() => productTranslations.data.product)}
              />
            );
          }}
        </TypedUpdateProductTranslations>
      )}
    </TypedProductTranslationDetails>
  );
};
TranslationsProducts.displayName = "TranslationsProducts";
export default TranslationsProducts;
