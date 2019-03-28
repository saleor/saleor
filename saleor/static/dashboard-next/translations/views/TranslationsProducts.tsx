import { stringify as stringifyQs } from "qs";
import * as React from "react";

import useNavigator from "../../hooks/useNavigator";
import { maybe } from "../../misc";
import { LanguageCodeEnum } from "../../types/globalTypes";
import TranslationsProductsPage from "../components/TranslationsProductsPage";
import { TypedProductTranslationDetails } from "../queries";

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

  return (
    <TypedProductTranslationDetails variables={{ id, language: languageCode }}>
      {productTranslations => (
        <TranslationsProductsPage
          activeField={params.activeField}
          disabled={productTranslations.loading}
          languageCode={languageCode}
          onEdit={field =>
            navigate(
              "?" +
                stringifyQs({
                  activeField: field
                })
            )
          }
          onSubmit={() => undefined}
          product={maybe(() => productTranslations.data.product)}
        />
      )}
    </TypedProductTranslationDetails>
  );
};
TranslationsProducts.displayName = "TranslationsProducts";
export default TranslationsProducts;
