import { storiesOf } from "@storybook/react";
import * as React from "react";

import PageList from "../../../pages/components/PageList";
import { pages } from "../../../pages/fixtures";

const pageInfo = {
  hasNextPage: false,
  hasPreviousPage: false
};

storiesOf("Pages / PageList", module)
  .add("with data", () => (
    <PageList
      pages={pages}
      pageInfo={pageInfo}
      onEditClick={() => {}}
      onNextPage={() => {}}
      onPreviousPage={() => {}}
      onShowPageClick={() => {}}
    />
  ))
  .add("without data", () => (
    <PageList
      pages={[]}
      pageInfo={pageInfo}
      onEditClick={() => {}}
      onNextPage={() => {}}
      onPreviousPage={() => {}}
      onShowPageClick={() => {}}
    />
  ))
  .add("when loading data", () => (
    <PageList
      pageInfo={pageInfo}
      onEditClick={() => {}}
      onNextPage={() => {}}
      onPreviousPage={() => {}}
      onShowPageClick={() => {}}
    />
  ));
