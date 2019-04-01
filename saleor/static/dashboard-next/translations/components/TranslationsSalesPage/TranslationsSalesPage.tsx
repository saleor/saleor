import * as React from "react";

import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton";
import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { SaleTranslationFragment } from "../../types/SaleTranslationFragment";
import TranslationFields from "../TranslationFields";

export interface TranslationsSalesPageProps {
  activeField: string;
  disabled: boolean;
  languageCode: string;
  sale: SaleTranslationFragment;
  saveButtonState: ConfirmButtonTransitionState;
  onEdit: (field: string) => void;
  onSubmit: (field: string, data: string) => void;
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
  sale,
  saveButtonState,
  onEdit,
  onSubmit
}) => (
  <Container>
    <PageHeader
      title={i18n.t('Translation Sale "{{ saleName }}" - {{ languageCode }}', {
        context: "sale translation page title",
        languageCode,
        saleName: maybe(() => sale.name, "...")
      })}
    />
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
