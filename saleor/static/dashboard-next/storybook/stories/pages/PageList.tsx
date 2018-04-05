import { storiesOf } from "@storybook/react";
import * as React from "react";
import Card from "material-ui/Card";

import PageList from "../../../page/components/PageList";

const pages = [
  {
    cursor: "YXJyYXljb25uZWN0aW9uOjA=",
    node: {
      id: "UGFnZTox",
      slug: "about",
      title: "About",
      isVisible: true
    }
  },
  {
    cursor: "YXJyYXljb25uZWN0aW9uOjE=",
    node: {
      id: "UGFnZToy",
      slug: "terms-of-use",
      title: "Terms of use",
      isVisible: false
    }
  }
];
const pageInfo = {
  hasPreviousPage: false,
  hasNextPage: false,
  startCursor: "YXJyYXljb25uZWN0aW9uOjA=",
  endCursor: "YXJyYXljb25uZWN0aW9uOjE="
};

storiesOf("Pages / PageList", module)
  .add("with data", () => (
    <Card>
      <PageList
        pages={pages}
        pageInfo={pageInfo}
        handlePreviousPage={() => {}}
        handleNextPage={() => {}}
        onEditClick={() => {}}
        onShowPageClick={() => {}}
      />
    </Card>
  ))
  .add("without data", () => (
    <Card>
      <PageList
        pages={[]}
        pageInfo={pageInfo}
        handlePreviousPage={() => {}}
        handleNextPage={() => {}}
        onEditClick={() => {}}
        onShowPageClick={() => {}}
      />
    </Card>
  ))
  .add("when loading data", () => (
    <Card>
      <PageList
        pageInfo={pageInfo}
        handlePreviousPage={() => {}}
        handleNextPage={() => {}}
        onEditClick={() => {}}
        onShowPageClick={() => {}}
      />
    </Card>
  ));
