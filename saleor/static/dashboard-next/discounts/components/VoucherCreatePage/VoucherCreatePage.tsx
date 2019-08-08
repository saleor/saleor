import React from "react";

import AppHeader from "@saleor/components/AppHeader";
import CardSpacer from "@saleor/components/CardSpacer";
import { ConfirmButtonTransitionState } from "@saleor/components/ConfirmButton";
import Container from "@saleor/components/Container";
import Form from "@saleor/components/Form";
import Grid from "@saleor/components/Grid";
import PageHeader from "@saleor/components/PageHeader";
import SaveButtonBar from "@saleor/components/SaveButtonBar";
import i18n from "../../../i18n";
import { UserError } from "../../../types";
import {
  DiscountValueTypeEnum,
  VoucherTypeEnum
} from "../../../types/globalTypes";
import { RequirementsPicker } from "../../types";
import VoucherDates from "../VoucherDates";
import VoucherInfo from "../VoucherInfo";
import VoucherLimits from "../VoucherLimits";
import VoucherRequirements from "../VoucherRequirements";
import VoucherTypes from "../VoucherTypes";

import VoucherValue from "../VoucherValue";
export interface FormData {
  applyOncePerCustomer: boolean;
  applyOncePerOrder: boolean;
  code: string;
  discountType: DiscountValueTypeEnum;
  endDate: string;
  endTime: string;
  hasEndDate: boolean;
  hasUsageLimit: boolean;
  minAmountSpent: string;
  minCheckoutItemsQuantity: string;
  requirementsPicker: RequirementsPicker;
  startDate: string;
  startTime: string;
  type: VoucherTypeEnum;
  usageLimit: string;
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
    applyOncePerCustomer: false,
    applyOncePerOrder: false,
    code: "",
    discountType: DiscountValueTypeEnum.FIXED,
    endDate: "",
    endTime: "",
    hasEndDate: false,
    hasUsageLimit: false,
    minAmountSpent: "0",
    minCheckoutItemsQuantity: "0",
    requirementsPicker: RequirementsPicker.NONE,
    startDate: "",
    startTime: "",
    type: VoucherTypeEnum.ENTIRE_ORDER,
    usageLimit: "0",
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
                onChange={change}
                variant="create"
              />
              <CardSpacer />
              <VoucherTypes
                data={data}
                disabled={disabled}
                errors={formErrors}
                onChange={change}
              />
              {data.discountType.toString() !== "SHIPPING" ? (
                <VoucherValue
                  data={data}
                  disabled={disabled}
                  defaultCurrency={defaultCurrency}
                  errors={formErrors}
                  onChange={change}
                  variant="create"
                />
              ) : null}
              <CardSpacer />
              <VoucherRequirements
                data={data}
                disabled={disabled}
                defaultCurrency={defaultCurrency}
                errors={formErrors}
                onChange={change}
              />
              <CardSpacer />
              <VoucherLimits
                data={data}
                disabled={disabled}
                defaultCurrency={defaultCurrency}
                errors={formErrors}
                onChange={change}
              />
              <CardSpacer />
              <VoucherDates
                data={data}
                disabled={disabled}
                defaultCurrency={defaultCurrency}
                errors={formErrors}
                onChange={change}
              />
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
