import * as React from "react";

import AppHeader from "../../../components/AppHeader";
import CardSpacer from "../../../components/CardSpacer";
import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import Grid from "../../../components/Grid";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
import i18n from "../../../i18n";
import { UserError } from "../../../types";
import {
  VoucherDiscountValueType,
  VoucherType
} from "../../../types/globalTypes";
import VoucherInfo from "../VoucherInfo";
import VoucherOptions from "../VoucherOptions";

export interface FormData {
  applyOncePerOrder: boolean;
  code: string;
  discountType: VoucherDiscountValueType;
  endDate: string;
  minAmountSpent: number;
  name: string;
  startDate: string;
  type: VoucherType;
  usageLimit: number;
  value: number;
}

export interface VoucherCreatePageProps {
  defaultCurrency: string;
  disabled: boolean;
  errors: UserError[];
  saveButtonBarState: ConfirmButtonTransitionState;
  onBack: () => void;
  onSubmit: (data: FormData) => void;
}

const VoucherCreatePage: React.StatelessComponent<VoucherCreatePageProps> = ({
  defaultCurrency,
  disabled,
  errors,
  saveButtonBarState,
  onBack,
  onSubmit
}) => {
  const initialForm: FormData = {
    applyOncePerOrder: false,
    code: "",
    discountType: VoucherDiscountValueType.FIXED,
    endDate: "",
    minAmountSpent: 0,
    name: "",
    startDate: "",
    type: VoucherType.VALUE,
    usageLimit: 0,
    value: 0
  };

  return (
    <Form errors={errors} initial={initialForm} onSubmit={onSubmit}>
      {({ change, data, errors: formErrors, hasChanged, submit }) => (
        <Container>
          <AppHeader onBack={onBack}>{i18n.t("Vouchers")}</AppHeader>
          <PageHeader title={i18n.t("Create Voucher")} />
          <Grid>
            <div>
              <VoucherInfo
                data={data}
                errors={formErrors}
                disabled={disabled}
                variant="create"
                onChange={change}
              />
              <CardSpacer />
              <VoucherOptions
                data={data}
                disabled={disabled}
                defaultCurrency={defaultCurrency}
                errors={formErrors}
                onChange={change}
              />
              <CardSpacer />
            </div>
          </Grid>
          <SaveButtonBar
            disabled={disabled || !hasChanged}
            onCancel={onBack}
            onSave={submit}
            state={saveButtonBarState}
          />
        </Container>
      )}
    </Form>
  );
};
VoucherCreatePage.displayName = "VoucherCreatePage";
export default VoucherCreatePage;
