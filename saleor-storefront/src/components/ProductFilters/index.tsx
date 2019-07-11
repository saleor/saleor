import "./scss/index.scss";

import * as React from "react";

import { Category_attributes_edges_node } from "../../views/Category/types/Category";
import { Collection_attributes_edges_node } from "../../views/Collection/types/Collection";
import { SearchProducts_attributes_edges_node } from "../../views/Search/types/SearchProducts";
import PriceRangeFilter from "../PriceRangeFilter";
import SelectField, { SelectValue } from "../SelectField";

export interface AttributeList {
  [attributeSlug: string]: string[];
}

export interface Filters {
  attributes: AttributeList;
  pageSize: number;
  sortBy: string;
  priceLte: number;
  priceGte: number;
}

export interface ProductFiltersProps {
  attributes:
    | Category_attributes_edges_node[]
    | Collection_attributes_edges_node[]
    | SearchProducts_attributes_edges_node[];
  filters: Filters;
  onPriceChange: (field: "priceLte" | "priceGte", value: number) => void;
  onAttributeFiltersChange: (attributeSlug: string, values: string[]) => void;
}

export const ProductFilters: React.FC<ProductFiltersProps> = ({
  attributes,
  filters,
  onAttributeFiltersChange,
  onPriceChange,
}) => (
  <div className="product-filters">
    <div className="container">
      <div className="product-filters__grid">
        {attributes.map(attribute => (
          <div key={attribute.id} className="product-filters__grid__filter">
            <SelectField
              value={
                filters.attributes[attribute.slug]
                  ? filters.attributes[attribute.slug].map(
                      attributeValueSlug => {
                        const attributeValue = attribute.values.find(
                          attributeValue =>
                            attributeValue.slug === attributeValueSlug
                        );
                        return {
                          label: attributeValue.name,
                          value: attributeValue.slug,
                        };
                      }
                    )
                  : []
              }
              placeholder={attribute.name}
              options={attribute.values.map(attributeValue => ({
                label: attributeValue.name,
                value: attributeValue.slug,
              }))}
              isMulti
              onChange={(values: SelectValue[]) =>
                onAttributeFiltersChange(
                  attribute.slug,
                  values.map(value => value.value)
                )
              }
            />
          </div>
        ))}
        <div className="product-filters__grid__filter">
          <PriceRangeFilter
            from={filters.priceGte}
            to={filters.priceLte}
            onChange={onPriceChange}
          />
        </div>
      </div>
    </div>
  </div>
);
