import Typography from "@material-ui/core/Typography";
import * as React from "react";

import AppHeader from "../../../components/AppHeader";
import CardSpacer from "../../../components/CardSpacer";
import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton";
import Container from "../../../components/Container";
import CountryList from "../../../components/CountryList";
import Form from "../../../components/Form";
import Grid from "../../../components/Grid";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
import { Tab } from "../../../components/Tab";
import TabContainer from "../../../components/Tab/TabContainer";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { ListProps, TabListActions, UserError } from "../../../types";
import {
  VoucherDiscountValueType,
  VoucherType
} from "../../../types/globalTypes";
import { VoucherDetails_voucher } from "../../types/VoucherDetails";
import DiscountCategories from "../DiscountCategories";
import DiscountCollections from "../DiscountCollections";
import DiscountProducts from "../DiscountProducts";
import VoucherInfo from "../VoucherInfo";
import VoucherOptions from "../VoucherOptions";
import VoucherSummary from "../VoucherSummary";

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
  minAmountSpent: number;
  name: string;
  startDate: string;
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
    endDate: maybe(() => voucher.endDate, ""),
    minAmountSpent: maybe(() => voucher.minAmountSpent.amount, 0),
    name: maybe(() => voucher.name, ""),
    startDate: maybe(() => voucher.startDate, ""),
    type: maybe(() => voucher.type, VoucherType.VALUE),
    usageLimit: maybe(() => voucher.usageLimit || 0, 0),
    value: maybe(() => voucher.discountValue, 0)
  };

  return (
    <Form errors={errors} initial={initialForm} onSubmit={onSubmit}>
      {({ change, data, errors: formErrors, hasChanged, submit }) => (
        <Container>
          <AppHeader onBack={onBack}>{i18n.t("Vouchers")}</AppHeader>
          <PageHeader title={maybe(() => voucher.name)} />
          <Grid>
            <div>
              <VoucherInfo
                data={data}
                disabled={disabled}
                errors={formErrors}
                variant="update"
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
              {data.type === VoucherType.CATEGORY ||
              data.type === VoucherType.COLLECTION ||
              data.type === VoucherType.PRODUCT ? (
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
                      toolbar={productListToolbar}
                    />
                  )}
                </>
              ) : data.type === VoucherType.SHIPPING ? (
                <CountryList
                  countries={maybe(() => voucher.countries)}
                  disabled={disabled}
                  emptyText={i18n.t("Voucher applies to all countries")}
                  title={
                    <>
                      {i18n.t("Countries assigned to {{ voucherName }}", {
                        voucherName: maybe(() => voucher.name)
                      })}
                      <Typography variant="caption">
                        {i18n.t("Vouchers limited to these countries")}
                      </Typography>
                    </>
                  }
                  onCountryAssign={onCountryAssign}
                  onCountryUnassign={onCountryUnassign}
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
