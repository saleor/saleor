import { storiesOf } from "@storybook/react";
import * as React from "react";

import { FilterContent, FilterContentProps } from "../../../components/Filter";
import { FieldType } from "../../../components/Filter/types";
import CardDecorator from "../../CardDecorator";
import Decorator from "../../Decorator";

const props: FilterContentProps = {
  filters: [
    {
      children: [],
      data: {
        type: FieldType.text
      },
      label: "Category",
      value: "category"
    },
    {
      children: [],
      data: {
        type: FieldType.text
      },
      label: "Product Type",
      value: "product-type"
    },
    {
      children: [],
      data: {
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
            type: FieldType.date
          },
          label: "Equal to",
          value: "date-equal"
        },
        {
          children: [],
          data: {
            type: FieldType.rangeDate
          },
          label: "Range",
          value: "date-range"
        }
      ],
      data: {
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
            type: FieldType.number
          },
          label: "Exactly",
          value: "price-exactly"
        },
        {
          children: [],
          data: {
            type: FieldType.rangePrice
          },
          label: "Range",
          value: "price-range"
        }
      ],
      data: {
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
