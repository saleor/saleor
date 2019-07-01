import Typography from "@material-ui/core/Typography";
import React from "react";

import AppHeader from "@saleor/components/AppHeader";
import CardSpacer from "@saleor/components/CardSpacer";
import { ConfirmButtonTransitionState } from "@saleor/components/ConfirmButton";
import Container from "@saleor/components/Container";
import CountryList from "@saleor/components/CountryList";
import Form from "@saleor/components/Form";
import Grid from "@saleor/components/Grid";
import PageHeader from "@saleor/components/PageHeader";
import SaveButtonBar from "@saleor/components/SaveButtonBar";
import { Tab, TabContainer } from "@saleor/components/Tab";
import i18n from "../../../i18n";
import { maybe, splitDateTime } from "../../../misc";
import { ListProps, TabListActions, UserError } from "../../../types";
import {
  VoucherDiscountValueType,
  VoucherType
} from "../../../types/globalTypes";
import { VoucherDetails_voucher } from "../../types/VoucherDetails";
import DiscountCategories from "../DiscountCategories";
import DiscountCollections from "../DiscountCollections";
import DiscountProducts from "../DiscountProducts";
import VoucherDates from "../VoucherDates";
import VoucherInfo from "../VoucherInfo";
import VoucherLimits from "../VoucherLimits";
import VoucherRequirements from "../VoucherRequirements";
import VoucherSummary from "../VoucherSummary";
import VoucherTypes from "../VoucherTypes";
import VoucherValue from "../VoucherValue";

export enum VoucherDetailsPageTab {
  categories = "categories",
  collections = "collections",
  products = "products"
}
export function voucherDetailsPageTab(tab: string): VoucherDetailsPageTab {
  return tab === VoucherDetailsPageTab.products
    ? VoucherDetailsPageTab.products
    : tab === VoucherDetailsPageTab.collections
    ? VoucherDetailsPageTab.collections
    : VoucherDetailsPageTab.categories;
}

export interface FormData {
  applyOncePerOrder: boolean;
  code: string;
  discountType: VoucherDiscountValueType;
  endDate: string;
  endTime: string;
  minAmountSpent: number;
  startDate: string;
  startTime: string;
  type: VoucherType;
  usageLimit: number;
  value: number;
}

export interface VoucherDetailsPageProps
  extends Pick<ListProps, Exclude<keyof ListProps, "onRowClick">>,
    TabListActions<
      "categoryListToolbar" | "collectionListToolbar" | "productListToolbar"
    > {
  activeTab: VoucherDetailsPageTab;
  defaultCurrency: string;
  errors: UserError[];
  saveButtonBarState: ConfirmButtonTransitionState;
  voucher: VoucherDetails_voucher;
  onBack: () => void;
  onCategoryAssign: () => void;
  onCategoryUnassign: (id: string) => void;
  onCategoryClick: (id: string) => () => void;
  onCollectionAssign: () => void;
  onCollectionUnassign: (id: string) => void;
  onCollectionClick: (id: string) => () => void;
  onCountryAssign: () => void;
  onCountryUnassign: (code: string) => void;
  onProductAssign: () => void;
  onProductUnassign: (id: string) => void;
  onProductClick: (id: string) => () => void;
  onRemove: () => void;
  onSubmit: (data: FormData) => void;
  onTabClick: (index: VoucherDetailsPageTab) => void;
}

const CategoriesTab = Tab(VoucherDetailsPageTab.categories);
const CollectionsTab = Tab(VoucherDetailsPageTab.collections);
const ProductsTab = Tab(VoucherDetailsPageTab.products);

const VoucherDetailsPage: React.StatelessComponent<VoucherDetailsPageProps> = ({
  activeTab,
  defaultCurrency,
  disabled,
  errors,
  pageInfo,
  saveButtonBarState,
  voucher,
  onBack,
  onCategoryAssign,
  onCategoryClick,
  onCategoryUnassign,
  onCountryAssign,
  onCountryUnassign,
  onCollectionAssign,
  onCollectionClick,
  onCollectionUnassign,
  onNextPage,
  onPreviousPage,
  onProductAssign,
  onProductClick,
  onProductUnassign,
  onTabClick,
  onRemove,
  onSubmit,
  toggle,
  toggleAll,
  selected,
  isChecked,
  categoryListToolbar,
  collectionListToolbar,
  productListToolbar
}) => {
  const initialForm: FormData = {
    applyOncePerOrder: maybe(() => voucher.applyOncePerOrder, false),
    code: maybe(() => voucher.code, ""),
    discountType: maybe(
      () => voucher.discountValueType,
      VoucherDiscountValueType.FIXED
    ),
    endDate: splitDateTime(maybe(() => voucher.endDate, "")).date,
    endTime: splitDateTime(maybe(() => voucher.endDate, "")).time,
    minAmountSpent: maybe(() => voucher.minAmountSpent.amount, 0),
    startDate: splitDateTime(maybe(() => voucher.startDate, "")).date,
    startTime: splitDateTime(maybe(() => voucher.startDate, "")).time,
    type: maybe(() => voucher.type, VoucherType.ENTIRE_ORDER),
    usageLimit: maybe(() => voucher.usageLimit || 0, 0),
    value: maybe(() => voucher.discountValue, 0)
  };

  return (
    <Form errors={errors} initial={initialForm} onSubmit={onSubmit}>
      {({ change, data, errors: formErrors, hasChanged, submit }) => (
        <Container>
          <AppHeader onBack={onBack}>{i18n.t("Vouchers")}</AppHeader>
          <PageHeader title={maybe(() => voucher.code)} />
          <Grid>
            <div>
              <VoucherInfo
                data={data}
                disabled={disabled}
                errors={formErrors}
                onChange={change}
              />
              <CardSpacer />
              <VoucherTypes
                data={data}
                disabled={disabled}
                errors={formErrors}
                onChange={change}
              />
              <CardSpacer />
              {data.discountType !== VoucherDiscountValueType.SHIPPING ? (
                <VoucherValue
                  data={data}
                  disabled={disabled}
                  defaultCurrency={defaultCurrency}
                  errors={formErrors}
                  onChange={change}
                />
              ) : null}
              <CardSpacer />
              {data.type === VoucherType.SPECIFIC_PRODUCT ? (
                <>
                  <TabContainer>
                    <CategoriesTab
                      isActive={activeTab === VoucherDetailsPageTab.categories}
                      changeTab={onTabClick}
                    >
                      {i18n.t("Categories ({{ number }})", {
                        number: maybe(
                          () => voucher.categories.totalCount.toString(),
                          "…"
                        )
                      })}
                    </CategoriesTab>
                    <CollectionsTab
                      isActive={activeTab === VoucherDetailsPageTab.collections}
                      changeTab={onTabClick}
                    >
                      {i18n.t("Collections ({{ number }})", {
                        number: maybe(
                          () => voucher.collections.totalCount.toString(),
                          "…"
                        )
                      })}
                    </CollectionsTab>
                    <ProductsTab
                      isActive={activeTab === VoucherDetailsPageTab.products}
                      changeTab={onTabClick}
                    >
                      {i18n.t("Products ({{ number }})", {
                        number: maybe(
                          () => voucher.products.totalCount.toString(),
                          "…"
                        )
                      })}
                    </ProductsTab>
                  </TabContainer>
                  <CardSpacer />
                  {activeTab === VoucherDetailsPageTab.categories ? (
                    <DiscountCategories
                      disabled={disabled}
                      onCategoryAssign={onCategoryAssign}
                      onCategoryUnassign={onCategoryUnassign}
                      onNextPage={onNextPage}
                      onPreviousPage={onPreviousPage}
                      onRowClick={onCategoryClick}
                      pageInfo={pageInfo}
                      discount={voucher}
                      isChecked={isChecked}
                      selected={selected}
                      toggle={toggle}
                      toggleAll={toggleAll}
                      toolbar={categoryListToolbar}
                    />
                  ) : activeTab === VoucherDetailsPageTab.collections ? (
                    <DiscountCollections
                      disabled={disabled}
                      onCollectionAssign={onCollectionAssign}
                      onCollectionUnassign={onCollectionUnassign}
                      onNextPage={onNextPage}
                      onPreviousPage={onPreviousPage}
                      onRowClick={onCollectionClick}
                      pageInfo={pageInfo}
                      discount={voucher}
                      isChecked={isChecked}
                      selected={selected}
                      toggle={toggle}
                      toggleAll={toggleAll}
                      toolbar={collectionListToolbar}
                    />
                  ) : (
                    <DiscountProducts
                      disabled={disabled}
                      onNextPage={onNextPage}
                      onPreviousPage={onPreviousPage}
                      onProductAssign={onProductAssign}
                      onProductUnassign={onProductUnassign}
                      onRowClick={onProductClick}
                      pageInfo={pageInfo}
                      discount={voucher}
                      isChecked={isChecked}
                      selected={selected}
                      toggle={toggle}
                      toggleAll={toggleAll}
                      toolbar={productListToolbar}
                    />
                  )}
                </>
              ) : data.discountType === VoucherDiscountValueType.SHIPPING ? (
                <CountryList
                  countries={maybe(() => voucher.countries)}
                  disabled={disabled}
                  emptyText={i18n.t("Voucher applies to all countries")}
                  title={
                    <>
                      {i18n.t("Countries")}
                      <Typography variant="caption">
                        {i18n.t("Vouchers limited to these countries")}
                      </Typography>
                    </>
                  }
                  onCountryAssign={onCountryAssign}
                  onCountryUnassign={onCountryUnassign}
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
