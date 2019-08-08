import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import { Theme } from "@material-ui/core/styles";
import AddIcon from "@material-ui/icons/Add";
import makeStyles from "@material-ui/styles/makeStyles";
import React from "react";

import { CategoryDetails_category_products_edges_node } from "@saleor/categories/types/CategoryDetails";
import ColumnPicker, {
  ColumnPickerChoice
} from "@saleor/components/ColumnPicker";
import Container from "@saleor/components/Container";
import PageHeader from "@saleor/components/PageHeader";
import ProductList from "@saleor/components/ProductList";
import { ProductListColumns } from "@saleor/config";
import useStateFromProps from "@saleor/hooks/useStateFromProps";
import i18n from "@saleor/i18n";
import { FilterPageProps, ListActions, PageListProps } from "@saleor/types";
import { toggle } from "@saleor/utils/lists";
import { ProductListUrlFilters } from "../../urls";
import ProductListFilter from "../ProductListFilter";

export interface ProductListPageProps
  extends PageListProps<ProductListColumns>,
    ListActions,
    FilterPageProps<ProductListUrlFilters> {
  currencySymbol: string;
  products: CategoryDetails_category_products_edges_node[];
}

const useStyles = makeStyles((theme: Theme) => ({
  columnPicker: {
    marginRight: theme.spacing.unit * 3
  }
}));

export const ProductListPage: React.FC<ProductListPageProps> = props => {
  const {
    currencySymbol,
    currentTab,
    defaultSettings,
    filtersList,
    filterTabs,
    initialSearch,
    settings,
    onAdd,
    onAll,
    onSearchChange,
    onFilterAdd,
    onFilterSave,
    onTabChange,
    onFilterDelete,
    onUpdateListSettings,
    ...listProps
  } = props;
  const classes = useStyles(props);
  const [selectedColumns, setSelectedColumns] = useStateFromProps(
    settings.columns
  );

  const handleCancel = React.useCallback(
    () => setSelectedColumns(settings.columns),
    [settings.columns]
  );

  const handleColumnToggle = (column: ProductListColumns) =>
    setSelectedColumns(prevSelectedColumns =>
      toggle(column, prevSelectedColumns, (a, b) => a === b)
    );

  const handleReset = () => setSelectedColumns(defaultSettings.columns);

  const handleSave = () => onUpdateListSettings("columns", selectedColumns);

  const columns: ColumnPickerChoice[] = [
    {
      label: i18n.t("Published"),
      value: "isPublished" as ProductListColumns
    },
    {
      label: i18n.t("Price"),
      value: "price" as ProductListColumns
    },
    {
      label: i18n.t("Type"),
      value: "productType" as ProductListColumns
    }
  ];

  return (
    <Container>
      <PageHeader title={i18n.t("Products")}>
        <ColumnPicker
          className={classes.columnPicker}
          columns={columns}
          selectedColumns={selectedColumns}
          onColumnToggle={handleColumnToggle}
          onCancel={handleCancel}
          onReset={handleReset}
          onSave={handleSave}
        />
        <Button onClick={onAdd} color="primary" variant="contained">
          {i18n.t("Add product")} <AddIcon />
        </Button>
      </PageHeader>
      <Card>
        <ProductListFilter
          allTabLabel={i18n.t("All Products")}
          currencySymbol={currencySymbol}
          currentTab={currentTab}
          filterLabel={i18n.t("Select all products where:")}
          filterTabs={filterTabs}
          filtersList={filtersList}
          initialSearch={initialSearch}
          searchPlaceholder={i18n.t("Search Products...")}
          onAll={onAll}
          onSearchChange={onSearchChange}
          onFilterAdd={onFilterAdd}
          onFilterSave={onFilterSave}
          onTabChange={onTabChange}
          onFilterDelete={onFilterDelete}
        />
        <ProductList
          {...listProps}
          settings={{ ...settings, columns: selectedColumns }}
          onUpdateListSettings={onUpdateListSettings}
        />
      </Card>
    </Container>
  );
};
ProductListPage.displayName = "ProductListPage";
export default ProductListPage;
