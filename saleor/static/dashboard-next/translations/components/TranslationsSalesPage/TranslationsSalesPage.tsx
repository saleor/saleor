import * as React from "react";

import AppHeader from "../../../components/AppHeader";
import Container from "../../../components/Container";
import LanguageSwitch from "../../../components/LanguageSwitch";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { LanguageCodeEnum } from "../../../types/globalTypes";
import { SaleTranslationFragment } from "../../types/SaleTranslationFragment";
import { TranslationsEntitiesPageProps } from "../../types/TranslationsEntitiesPage";
import TranslationFields from "../TranslationFields";

export interface TranslationsSalesPageProps
  extends TranslationsEntitiesPageProps {
  sale: SaleTranslationFragment;
}

export const fieldNames = {
  name: "name"
};

const TranslationsSalesPage: React.StatelessComponent<
  TranslationsSalesPageProps
> = ({
  activeField,
  disabled,
  languageCode,
  languages,
  sale,
  saveButtonState,
  onBack,
  onEdit,
  onLanguageChange,
  onSubmit
}) => (
  <Container>
    <AppHeader onBack={onBack}>{i18n.t("Translations")}</AppHeader>
    <PageHeader
      title={i18n.t('Translation Sale "{{ saleName }}" - {{ languageCode }}', {
        context: "sale translation page title",
        languageCode,
        saleName: maybe(() => sale.name, "...")
      })}
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
          displayName: i18n.t("Sale Name"),
          name: fieldNames.name,
          translation: maybe(() =>
            sale.translation ? sale.translation.name : null
          ),
          type: "short" as "short",
          value: maybe(() => sale.name)
        }
      ]}
      saveButtonState={saveButtonState}
      onEdit={onEdit}
      onSubmit={onSubmit}
    />
  </Container>
);
TranslationsSalesPage.displayName = "TranslationsSalesPage";
export default TranslationsSalesPage;
