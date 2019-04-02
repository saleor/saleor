import * as React from "react";

import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton";
import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { VoucherTranslationFragment } from "../../types/VoucherTranslationFragment";
import TranslationFields from "../TranslationFields";
import AppHeader from "../../../components/AppHeader";

export interface TranslationsVouchersPageProps {
  activeField: string;
  disabled: boolean;
  languageCode: string;
  voucher: VoucherTranslationFragment;
  saveButtonState: ConfirmButtonTransitionState;
  onBack: () => void;
  onEdit: (field: string) => void;
  onSubmit: (field: string, data: string) => void;
}

export const fieldNames = {
  name: "name"
};

const TranslationsVouchersPage: React.StatelessComponent<
  TranslationsVouchersPageProps
> = ({
  activeField,
  disabled,
  languageCode,
  voucher,
  saveButtonState,
  onBack,
  onEdit,
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
    />
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
