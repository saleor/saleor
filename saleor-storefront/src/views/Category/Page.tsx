import "./scss/index.scss";

import * as React from "react";

import {
  Breadcrumbs,
  extractBreadcrumbs,
  ProductsFeatured,
  ProductsList
} from "../../components";
import { Filters, ProductFilters } from "../../components/ProductFilters";

import { maybe } from "../../core/utils";
import {
  Category_attributes_edges_node,
  Category_category,
  Category_products
} from "./types/Category";

interface PageProps {
  attributes: Category_attributes_edges_node[];
  category: Category_category;
  displayLoader: boolean;
  filters: Filters;
  hasNextPage: boolean;
  products: Category_products;
  onLoadMore: () => void;
  onPriceChange: (field: "priceLte" | "priceGte", value: number) => void;
  onAttributeFiltersChange: (attributeSlug: string, values: string[]) => void;
  onOrder: (order: string) => void;
}

const Page: React.FC<PageProps> = ({
  attributes,
  category,
  displayLoader,
  filters,
  hasNextPage,
  onLoadMore,
  products,
  onAttributeFiltersChange,
  onPriceChange,
  onOrder,
}) => {
  const canDisplayProducts = maybe(
    () => !!products.edges && products.totalCount !== undefined
  );
  const hasProducts = canDisplayProducts && !!products.totalCount;

  return (
    <div className="category">
      <div
        className="category__header"
        style={
          category.backgroundImage
            ? { backgroundImage: `url(${category.backgroundImage.url})` }
            : undefined
        }
      >
        <span className="category__header__title">
          <h1>{category.name}</h1>
        </span>
      </div>

      <div className="container">
        <Breadcrumbs breadcrumbs={extractBreadcrumbs(category)} />
      </div>

      {hasProducts && (
        <ProductFilters
          filters={filters}
          attributes={attributes}
          onAttributeFiltersChange={onAttributeFiltersChange}
          onPriceChange={onPriceChange}
        />
      )}

      {canDisplayProducts && (
        <ProductsList
          displayLoader={displayLoader}
          filters={filters}
          hasNextPage={hasNextPage}
          onLoadMore={onLoadMore}
          onOrder={onOrder}
          products={products.edges.map(edge => edge.node)}
          totalCount={products.totalCount}
        />
      )}
      {!hasProducts && <ProductsFeatured title="You might like" />}
    </div>
  );
};

export default Page;
