import { storiesOf } from "@storybook/react";
import * as React from "react";

import ColumnPicker, {
  ColumnPickerProps
} from "@saleor/components/ColumnPicker";
import { ColumnPickerChoice } from "@saleor/components/ColumnPicker/ColumnPickerContent";
import CardDecorator from "@saleor/storybook/CardDecorator";
import Decorator from "../../Decorator";

const columns: ColumnPickerChoice[] = [
  { label: "Name", value: "name" },
  { label: "Value", value: "value" },
  { label: "Type", value: "type" },
  { label: "Size", value: "size" },
  { label: "Status", value: "isPublished" },
  { label: "Price", value: "price" },
  { label: "Digital", value: "isDigital" },
  ...Array(15)
    .fill(0)
    .map((_, index) => ({
      label: "Attribute " + (index + 1),
      value: "attribute_" + index
    }))
];

const props: ColumnPickerProps = {
  columns,
  initial: true,
  onCancel: () => undefined,
  onColumnToggle: () => undefined,
  onReset: () => undefined,
  onSave: () => undefined,
  selectedColumns: [1, 3, 4, 6].map(index => columns[index].value)
};

storiesOf("Generics / Column picker", module)
  .addDecorator(storyFn => (
    <div style={{ display: "flex ", justifyContent: "center" }}>
      {storyFn()}
    </div>
  ))
  .addDecorator(CardDecorator)
  .addDecorator(Decorator)
  .add("default", () => <ColumnPicker {...props} />);
