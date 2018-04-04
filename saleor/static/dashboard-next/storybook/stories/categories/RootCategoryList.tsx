import { storiesOf } from "@storybook/react";
import { DialogContentText } from "material-ui/Dialog";
import * as React from "react";

import RootCategoryList from "../../../category/components/RootCategoryList";

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

storiesOf("Categories / RootCategoryList", module)
  .add("with initial data", () => (
    <RootCategoryList
      categories={categories}
      onClick={() => {}}
      onCreate={() => {}}
    />
  ))
  .add("without initial data", () => (
    <RootCategoryList categories={[]} onClick={() => {}} onCreate={() => {}} />
  ))
  .add("when loading data", () => (
    <RootCategoryList onClick={() => {}} onCreate={() => {}} />
  ));
