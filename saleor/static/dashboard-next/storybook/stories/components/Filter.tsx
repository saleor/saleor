import { storiesOf } from "@storybook/react";
import React from "react";

import {
  FieldType,
  FilterContent,
  FilterContentProps
} from "@saleor/components/Filter";
import CardDecorator from "../../CardDecorator";
import Decorator from "../../Decorator";

const props: FilterContentProps = {
  currencySymbol: "USD",
  filters: [
    {
      children: [],
      data: {
        fieldLabel: "Category Name",
        type: FieldType.text
      },
      label: "Category",
      value: "category"
    },
    {
      children: [],
      data: {
        fieldLabel: "Product Type Name",
        type: FieldType.text
      },
      label: "Product Type",
      value: "product-type"
    },
    {
      children: [],
      data: {
        fieldLabel: "Status",
        options: [
          {
            label: "Published",
            value: true
          },
          {
            label: "Hidden",
            value: false
          }
        ],
        type: FieldType.select
      },
      label: "Published",
      value: "published"
    },
    {
      children: [],
      data: {
        fieldLabel: "Stock",
        type: FieldType.range
      },
      label: "Stock",
      value: "stock"
    },
    {
      children: [
        {
          children: [],
          data: {
            fieldLabel: "Equal to",
            type: FieldType.date
          },
          label: "Equal to",
          value: "date-equal"
        },
        {
          children: [],
          data: {
            fieldLabel: "Range",
            type: FieldType.rangeDate
          },
          label: "Range",
          value: "date-range"
        }
      ],
      data: {
        fieldLabel: "Date",
        type: FieldType.select
      },
      label: "Date",
      value: "date"
    },
    {
      children: [
        {
          children: [],
          data: {
            fieldLabel: "Exactly",
            type: FieldType.price
          },
          label: "Exactly",
          value: "price-exactly"
        },
        {
          children: [],
          data: {
            fieldLabel: "Range",
            type: FieldType.rangePrice
          },
          label: "Range",
          value: "price-range"
        }
      ],
      data: {
        fieldLabel: "Price",
        type: FieldType.select
      },
      label: "Price",
      value: "price"
    }
  ],
  onSubmit: () => undefined
};

storiesOf("Generics / Filter", module)
  .addDecorator(CardDecorator)
  .addDecorator(Decorator)
  .add("default", () => <FilterContent {...props} />);
