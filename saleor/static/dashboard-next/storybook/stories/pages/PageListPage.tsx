import { storiesOf } from "@storybook/react";
import * as React from "react";

import PageList from "../../../pages/components/PageListPage";
import { pages } from "../../../pages/fixtures";

const pageInfo = {
  hasNextPage: false,
  hasPreviousPage: false
};

storiesOf("Views / Pages / Page list", module)
  .add("with data", () => (
    <PageList
      pages={pages}
      pageInfo={pageInfo}
      onBack={() => {}}
      onEditPage={() => {}}
      onNextPage={() => {}}
      onPreviousPage={() => {}}
      onShowPage={() => {}}
    />
  ))
  .add("without data", () => (
    <PageList
      pages={[]}
      pageInfo={pageInfo}
      onBack={() => {}}
      onEditPage={() => {}}
      onNextPage={() => {}}
      onPreviousPage={() => {}}
      onShowPage={() => {}}
    />
  ))
  .add("when loading data", () => (
    <PageList
      pageInfo={pageInfo}
      onBack={() => {}}
      onEditPage={() => {}}
      onNextPage={() => {}}
      onPreviousPage={() => {}}
      onShowPage={() => {}}
    />
  ));
