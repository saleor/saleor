import { storiesOf } from "@storybook/react";
import { DialogContentText } from "material-ui/Dialog";
import * as React from "react";

import CategorySubcategories from "../../../category/components/CategorySubcategories";

const categories = [
  {
    id: "123123",
    name: "Lorem ipsum dolor"
  },
  {
    id: "876752",
    name: "Mauris vehicula tortor vulputate"
  }
];

storiesOf("Categories / CategorySubcategories", module)
  .add("with initial data", () => (
    <CategorySubcategories
      subcategories={categories}
      onClickSubcategory={() => {}}
      onCreate={() => {}}
    />
  ))
  .add("without initial data", () => (
    <CategorySubcategories
      subcategories={[]}
      onClickSubcategory={() => {}}
      onCreate={() => {}}
    />
  ))
  .add("when loading data", () => (
    <CategorySubcategories onClickSubcategory={() => {}} onCreate={() => {}} />
  ));
