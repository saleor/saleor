import * as React from "react";

import CardSpacer from "../../../components/CardSpacer";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import Grid from "../../../components/Grid";
import PageHeader from "../../../components/PageHeader";
import { Tab } from "../../../components/Tab";
import TabContainer from "../../../components/Tab/TabContainer";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { ListProps } from "../../../types";
import { SaleType } from "../../../types/globalTypes";
import { SaleDetails_sale } from "../../types/SaleDetails";
import SaleInfo from "../SaleInfo";
import SalePricing from "../SalePricing";
import SaleSummary from "../SaleSummary";
import SaleCategories from "../SaleCategories";
import SaleCollections from "../SaleCollections";
import SaleProducts from "../SaleProducts";

export interface FormData {
  name: string;
  startDate: string;
  endDate: string;
  value: string;
  type: SaleType;
}

export enum SaleDetailsPageTab {
  "categories",
  "collections",
  "products"
}

export interface SaleDetailsPageProps extends ListProps {
  activeTab: SaleDetailsPageTab;
  defaultCurrency: string;
  sale: SaleDetails_sale;
  onBack: () => void;
  onRemove: () => void;
  onSubmit: (data: FormData) => void;
  onTabClick: (index: SaleDetailsPageTab) => void;
}

const CategoriesTab = Tab(SaleDetailsPageTab.categories);
const CollectionsTab = Tab(SaleDetailsPageTab.collections);
const ProductsTab = Tab(SaleDetailsPageTab.products);

const SaleDetailsPage: React.StatelessComponent<SaleDetailsPageProps> = ({
  activeTab,
  onTabClick,
  defaultCurrency,
  disabled,
  sale,
  pageInfo,
  onBack,
  onNextPage,
  onPreviousPage,
  onRemove,
  onRowClick,
  onSubmit
}) => {
  const initialForm: FormData = {
    endDate: maybe(() => sale.endDate),
    name: maybe(() => sale.name),
    startDate: maybe(() => sale.startDate),
    type: maybe(() => sale.type),
    value: maybe(() => sale.value.toString())
  };
  return (
    <Form initial={initialForm} onSubmit={onSubmit}>
      {({ change, data, errors, hasChanged, submit }) => (
        <Container width="md">
          <PageHeader title={maybe(() => sale.name)} onBack={onBack} />
          <Grid>
            <div>
              <SaleInfo data={data} disabled={disabled} onChange={change} />
              <CardSpacer />
              <SalePricing
                data={data}
                defaultCurrency={defaultCurrency}
                disabled={disabled}
                onChange={change}
              />
              <CardSpacer />
              <TabContainer>
                <CategoriesTab
                  isActive={activeTab === SaleDetailsPageTab.categories}
                  changeTab={onTabClick}
                >
                  {i18n.t("Categories")}
                </CategoriesTab>
                <CollectionsTab
                  isActive={activeTab === SaleDetailsPageTab.collections}
                  changeTab={onTabClick}
                >
                  {i18n.t("Collections")}
                </CollectionsTab>
                <ProductsTab
                  isActive={activeTab === SaleDetailsPageTab.products}
                  changeTab={onTabClick}
                >
                  {i18n.t("Products")}
                </ProductsTab>
              </TabContainer>
              <CardSpacer />
              {activeTab === SaleDetailsPageTab.categories ? (
                <SaleCategories
                  disabled={disabled}
                  onNextPage={onNextPage}
                  onPreviousPage={onPreviousPage}
                  onRowClick={onRowClick}
                  pageInfo={pageInfo}
                  sale={sale}
                />
              ) : activeTab === SaleDetailsPageTab.collections ? (
                <SaleCollections
                  disabled={disabled}
                  onNextPage={onNextPage}
                  onPreviousPage={onPreviousPage}
                  onRowClick={onRowClick}
                  pageInfo={pageInfo}
                  sale={sale}
                />
              ) : (
                <SaleProducts
                  disabled={disabled}
                  onNextPage={onNextPage}
                  onPreviousPage={onPreviousPage}
                  onRowClick={onRowClick}
                  pageInfo={pageInfo}
                  sale={sale}
                />
              )}
            </div>
            <div>
              <SaleSummary defaultCurrency={defaultCurrency} sale={sale} />
            </div>
          </Grid>
        </Container>
      )}
    </Form>
  );
};
SaleDetailsPage.displayName = "SaleDetailsPage";
export default SaleDetailsPage;
