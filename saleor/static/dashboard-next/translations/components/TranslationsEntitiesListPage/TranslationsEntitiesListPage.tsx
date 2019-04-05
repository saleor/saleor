import Card from "@material-ui/core/Card";
import * as React from "react";

import AppHeader from "../../../components/AppHeader";
import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import { ShopInfo_shop_languages } from "../../../components/Shop/types/ShopInfo";
import FilterTabs, { FilterTab } from "../../../components/TableFilter";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { TranslatableEntities } from "../../urls";

export interface TranslationsEntitiesListPageProps {
  children: React.ReactNode;
  filters: TranslationsEntitiesFilters;
  language: ShopInfo_shop_languages;
  onBack: () => void;
}

export interface TranslationsEntitiesFilters {
  current: TranslationsEntitiesListFilterTab;
  onCategoriesTabClick: () => void;
  onCollectionsTabClick: () => void;
  onProductsTabClick: () => void;
  onSalesTabClick: () => void;
  onVouchersTabClick: () => void;
  onPagesTabClick: () => void;
  onProductTypesTabClick: () => void;
}

export type TranslationsEntitiesListFilterTab = keyof typeof TranslatableEntities;

const TranslationsEntitiesListPage: React.StatelessComponent<
  TranslationsEntitiesListPageProps
> = ({ filters, language, onBack, children }) => (
  <Container>
    <AppHeader onBack={onBack}>{i18n.t("Languages")}</AppHeader>
    <PageHeader
      title={i18n.t("Translations to {{ language }}", {
        context: "object translation page header",
        language: maybe(() => language.language, "...")
      })}
    />
    <Card>
      <FilterTabs
        currentTab={([
          "categories",
          "collections",
          "products",
          "sales",
          "vouchers",
          "pages",
          "productTypes"
        ] as TranslationsEntitiesListFilterTab[]).indexOf(filters.current)}
      >
        <FilterTab
          label={i18n.t("Categories")}
          onClick={filters.onCategoriesTabClick}
        />
        <FilterTab
          label={i18n.t("Collections")}
          onClick={filters.onCollectionsTabClick}
        />
        <FilterTab
          label={i18n.t("Products")}
          onClick={filters.onProductsTabClick}
        />
        <FilterTab label={i18n.t("Sales")} onClick={filters.onSalesTabClick} />
        <FilterTab
          label={i18n.t("Vouchers")}
          onClick={filters.onVouchersTabClick}
        />
        <FilterTab label={i18n.t("Pages")} onClick={filters.onPagesTabClick} />
        <FilterTab
          label={i18n.t("Product Types")}
          onClick={filters.onProductTypesTabClick}
        />
      </FilterTabs>
      {children}
    </Card>
  </Container>
);
TranslationsEntitiesListPage.displayName = "TranslationsEntitiesListPage";
export default TranslationsEntitiesListPage;
