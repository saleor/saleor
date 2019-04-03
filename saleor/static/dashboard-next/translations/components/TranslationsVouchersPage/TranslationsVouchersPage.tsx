import * as React from "react";

import AppHeader from "../../../components/AppHeader";
import Container from "../../../components/Container";
import LanguageSwitch from "../../../components/LanguageSwitch";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { LanguageCodeEnum } from "../../../types/globalTypes";
import { TranslationsEntitiesPageProps } from "../../types/TranslationsEntitiesPage";
import { VoucherTranslationFragment } from "../../types/VoucherTranslationFragment";
import TranslationFields from "../TranslationFields";

export interface TranslationsVouchersPageProps
  extends TranslationsEntitiesPageProps {
  voucher: VoucherTranslationFragment;
}

export const fieldNames = {
  name: "name"
};

const TranslationsVouchersPage: React.StatelessComponent<
  TranslationsVouchersPageProps
> = ({
  activeField,
  disabled,
  languages,
  languageCode,
  voucher,
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
        'Translation Voucher "{{ voucherName }}" - {{ languageCode }}',
        {
          context: "voucher translation page title",
          languageCode,
          voucherName: maybe(() => voucher.name, "...")
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
          displayName: i18n.t("Voucher Name"),
          name: fieldNames.name,
          translation: maybe(() =>
            voucher.translation ? voucher.translation.name : null
          ),
          type: "short" as "short",
          value: maybe(() => voucher.name)
        }
      ]}
      saveButtonState={saveButtonState}
      onEdit={onEdit}
      onSubmit={onSubmit}
    />
  </Container>
);
TranslationsVouchersPage.displayName = "TranslationsVouchersPage";
export default TranslationsVouchersPage;
