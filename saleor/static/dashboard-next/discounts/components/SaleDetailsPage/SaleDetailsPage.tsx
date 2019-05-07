import * as React from "react";

import AppHeader from "../../../components/AppHeader";
import CardSpacer from "../../../components/CardSpacer";
import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import Grid from "../../../components/Grid";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
import { Tab } from "../../../components/Tab";
import TabContainer from "../../../components/Tab/TabContainer";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { ListProps, TabListActions, UserError } from "../../../types";
import { SaleType } from "../../../types/globalTypes";
import { SaleDetails_sale } from "../../types/SaleDetails";
import DiscountCategories from "../DiscountCategories";
import DiscountCollections from "../DiscountCollections";
import DiscountProducts from "../DiscountProducts";
import SaleInfo from "../SaleInfo";
import SalePricing from "../SalePricing";
import SaleSummary from "../SaleSummary";

export interface FormData {
  name: string;
  startDate: string;
  endDate: string;
  value: string;
  type: SaleType;
}

export enum SaleDetailsPageTab {
  categories = "categories",
  collections = "collections",
  products = "products"
}
export function saleDetailsPageTab(tab: string): SaleDetailsPageTab {
  return tab === SaleDetailsPageTab.products
    ? SaleDetailsPageTab.products
    : tab === SaleDetailsPageTab.collections
    ? SaleDetailsPageTab.collections
    : SaleDetailsPageTab.categories;
}

export interface SaleDetailsPageProps
  extends Pick<ListProps, Exclude<keyof ListProps, "onRowClick">>,
    TabListActions<
      "categoryListToolbar" | "collectionListToolbar" | "productListToolbar"
    > {
  activeTab: SaleDetailsPageTab;
  defaultCurrency: string;
  errors: UserError[];
  sale: SaleDetails_sale;
  saveButtonBarState: ConfirmButtonTransitionState;
  onBack: () => void;
  onCategoryAssign: () => void;
  onCategoryUnassign: (id: string) => void;
  onCategoryClick: (id: string) => () => void;
  onCollectionAssign: () => void;
  onCollectionUnassign: (id: string) => void;
  onCollectionClick: (id: string) => () => void;
  onProductAssign: () => void;
  onProductUnassign: (id: string) => void;
  onProductClick: (id: string) => () => void;
  onRemove: () => void;
  onSubmit: (data: FormData) => void;
  onTabClick: (index: SaleDetailsPageTab) => void;
}

const CategoriesTab = Tab(SaleDetailsPageTab.categories);
const CollectionsTab = Tab(SaleDetailsPageTab.collections);
const ProductsTab = Tab(SaleDetailsPageTab.products);

const SaleDetailsPage: React.StatelessComponent<SaleDetailsPageProps> = ({
  activeTab,
  defaultCurrency,
  disabled,
  errors,
  onRemove,
  onSubmit,
  onTabClick,
  pageInfo,
  sale,
  saveButtonBarState,
  onBack,
  onCategoryAssign,
  onCategoryUnassign,
  onCategoryClick,
  onCollectionAssign,
  onCollectionUnassign,
  onCollectionClick,
  onNextPage,
  onPreviousPage,
  onProductAssign,
  onProductUnassign,
  onProductClick,
  categoryListToolbar,
  collectionListToolbar,
  productListToolbar,
  isChecked,
  selected,
  toggle
}) => {
  const initialForm: FormData = {
    endDate: maybe(() => (sale.endDate ? sale.endDate : ""), ""),
    name: maybe(() => sale.name, ""),
    startDate: maybe(() => sale.startDate, ""),
    type: maybe(() => sale.type, SaleType.FIXED),
    value: maybe(() => sale.value.toString(), "")
  };
  return (
    <Form errors={errors} initial={initialForm} onSubmit={onSubmit}>
      {({ change, data, errors: formErrors, hasChanged, submit }) => (
        <Container>
          <AppHeader onBack={onBack}>{i18n.t("Sales")}</AppHeader>
          <PageHeader title={maybe(() => sale.name)} />
          <Grid>
            <div>
              <SaleInfo
                data={data}
                disabled={disabled}
                errors={formErrors}
                onChange={change}
              />
              <CardSpacer />
              <SalePricing
                data={data}
                defaultCurrency={defaultCurrency}
                disabled={disabled}
                errors={formErrors}
                onChange={change}
              />
              <CardSpacer />
              <TabContainer>
                <CategoriesTab
                  isActive={activeTab === SaleDetailsPageTab.categories}
                  changeTab={onTabClick}
                >
                  {i18n.t("Categories ({{ number }})", {
                    number: maybe(
                      () => sale.categories.totalCount.toString(),
                      "…"
                    )
                  })}
                </CategoriesTab>
                <CollectionsTab
                  isActive={activeTab === SaleDetailsPageTab.collections}
                  changeTab={onTabClick}
                >
                  {i18n.t("Collections ({{ number }})", {
                    number: maybe(
                      () => sale.collections.totalCount.toString(),
                      "…"
                    )
                  })}
                </CollectionsTab>
                <ProductsTab
                  isActive={activeTab === SaleDetailsPageTab.products}
                  changeTab={onTabClick}
                >
                  {i18n.t("Products ({{ number }})", {
                    number: maybe(
                      () => sale.products.totalCount.toString(),
                      "…"
                    )
                  })}
                </ProductsTab>
              </TabContainer>
              <CardSpacer />
              {activeTab === SaleDetailsPageTab.categories ? (
                <DiscountCategories
                  disabled={disabled}
                  onCategoryAssign={onCategoryAssign}
                  onCategoryUnassign={onCategoryUnassign}
                  onNextPage={onNextPage}
                  onPreviousPage={onPreviousPage}
                  onRowClick={onCategoryClick}
                  pageInfo={pageInfo}
                  discount={sale}
                  isChecked={isChecked}
                  selected={selected}
                  toggle={toggle}
                  toolbar={categoryListToolbar}
                />
              ) : activeTab === SaleDetailsPageTab.collections ? (
                <DiscountCollections
                  disabled={disabled}
                  onCollectionAssign={onCollectionAssign}
                  onCollectionUnassign={onCollectionUnassign}
                  onNextPage={onNextPage}
                  onPreviousPage={onPreviousPage}
                  onRowClick={onCollectionClick}
                  pageInfo={pageInfo}
                  discount={sale}
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
                  discount={sale}
                  isChecked={isChecked}
                  selected={selected}
                  toggle={toggle}
                  toolbar={productListToolbar}
                />
              )}
            </div>
            <div>
              <SaleSummary defaultCurrency={defaultCurrency} sale={sale} />
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
SaleDetailsPage.displayName = "SaleDetailsPage";
export default SaleDetailsPage;
