import * as React from "react";

import CardSpacer from "../../../components/CardSpacer";
import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import Grid from "../../../components/Grid";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
import { maybe } from "../../../misc";
import { ListProps } from "../../../types";
import {
  VoucherDiscountValueType,
  VoucherType
} from "../../../types/globalTypes";
import { VoucherDetails_voucher } from "../../types/VoucherDetails";
import DiscountCategories from "../DiscountCategories";
import DiscountCollections from "../DiscountCollections";
import DiscountProducts from "../DiscountProducts";
import VoucherCountries from "../VoucherCountries";
import VoucherInfo from "../VoucherInfo";
import VoucherOptions from "../VoucherOptions";
import VoucherSummary from "../VoucherSummary";

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

export interface VoucherDetailsPageProps
  extends Pick<ListProps, Exclude<keyof ListProps, "onRowClick">> {
  defaultCurrency: string;
  saveButtonBarState: ConfirmButtonTransitionState;
  voucher: VoucherDetails_voucher;
  onBack: () => void;
  onCategoryAssign: () => void;
  onCategoryClick: (id: string) => () => void;
  onCountryAssign: () => void;
  onCountryUnassign: (code: string) => () => void;
  onCollectionAssign: () => void;
  onCollectionClick: (id: string) => () => void;
  onProductAssign: () => void;
  onProductClick: (id: string) => () => void;
  onRemove: () => void;
  onSubmit: (data: FormData) => void;
}

const VoucherDetailsPage: React.StatelessComponent<VoucherDetailsPageProps> = ({
  defaultCurrency,
  disabled,
  pageInfo,
  saveButtonBarState,
  voucher,
  onBack,
  onCategoryAssign,
  onCategoryClick,
  onCountryAssign,
  onCountryUnassign,
  onCollectionAssign,
  onCollectionClick,
  onNextPage,
  onPreviousPage,
  onProductAssign,
  onProductClick,
  onRemove,
  onSubmit
}) => {
  const initialForm: FormData = {
    applyOncePerOrder: maybe(() => voucher.applyOncePerOrder, false),
    code: maybe(() => voucher.code, ""),
    discountType: maybe(
      () => voucher.discountValueType,
      VoucherDiscountValueType.FIXED
    ),
    endDate: maybe(() => voucher.endDate, ""),
    minAmountSpent: maybe(() => voucher.minAmountSpent.amount, 0),
    name: maybe(() => voucher.name, ""),
    startDate: maybe(() => voucher.startDate, ""),
    type: maybe(() => voucher.type, VoucherType.VALUE),
    usageLimit: maybe(() => voucher.usageLimit || 0, 0),
    value: maybe(() => voucher.discountValue, 0)
  };

  return (
    <Form initial={initialForm} onSubmit={onSubmit}>
      {({ change, data, errors: formErrors, hasChanged, submit }) => (
        <Container width="md">
          <PageHeader title={maybe(() => voucher.name)} onBack={onBack} />
          <Grid>
            <div>
              <VoucherInfo data={data} disabled={disabled} onChange={change} />
              <CardSpacer />
              <VoucherOptions
                data={data}
                disabled={disabled}
                defaultCurrency={defaultCurrency}
                errors={formErrors}
                onChange={change}
              />
              <CardSpacer />
              {data.type === VoucherType.CATEGORY ? (
                <DiscountCategories
                  disabled={disabled}
                  onCategoryAssign={onCategoryAssign}
                  onNextPage={onNextPage}
                  onPreviousPage={onPreviousPage}
                  onRowClick={onCategoryClick}
                  pageInfo={pageInfo}
                  discount={voucher}
                />
              ) : data.type === VoucherType.COLLECTION ? (
                <DiscountCollections
                  disabled={disabled}
                  onCollectionAssign={onCollectionAssign}
                  onNextPage={onNextPage}
                  onPreviousPage={onPreviousPage}
                  onRowClick={onCollectionClick}
                  pageInfo={pageInfo}
                  discount={voucher}
                />
              ) : data.type === VoucherType.PRODUCT ? (
                <DiscountProducts
                  disabled={disabled}
                  onNextPage={onNextPage}
                  onPreviousPage={onPreviousPage}
                  onProductAssign={onProductAssign}
                  onRowClick={onProductClick}
                  pageInfo={pageInfo}
                  discount={voucher}
                />
              ) : data.type === VoucherType.SHIPPING ? (
                <VoucherCountries
                  disabled={disabled}
                  onCountryAssign={onCountryAssign}
                  onCountryUnassign={onCountryUnassign}
                  voucher={voucher}
                />
              ) : null}
            </div>
            <div>
              <VoucherSummary
                defaultCurrency={defaultCurrency}
                voucher={voucher}
              />
            </div>
          </Grid>
          <SaveButtonBar
            disabled={disabled || !hasChanged}
            onCancel={onBack}
            onDelete={onRemove}
            onSave={submit}
            state={saveButtonBarState}
          />
        </Container>
      )}
    </Form>
  );
};
VoucherDetailsPage.displayName = "VoucherDetailsPage";

export default VoucherDetailsPage;
