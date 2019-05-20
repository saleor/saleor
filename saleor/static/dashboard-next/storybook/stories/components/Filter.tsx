import { storiesOf } from "@storybook/react";
import * as React from "react";

import { FilterContent, FilterContentProps } from "../../../components/Filter";
import { FieldType } from "../../../components/Filter/types";
import CardDecorator from "../../CardDecorator";
import Decorator from "../../Decorator";

const props: FilterContentProps = {
  filters: [
    {
      children: [
        {
          children: [],
          data: {
            type: FieldType.date
          },
          label: "Exactly",
          value: "date-exactly"
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
  onSubmit: data => console.log(data)
};

storiesOf("Generics / Filter", module)
  .addDecorator(CardDecorator)
  .addDecorator(Decorator)
  .add("default", () => <FilterContent {...props} />);
