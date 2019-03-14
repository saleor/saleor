import { storiesOf } from "@storybook/react";
import * as React from "react";

import { pageListProps } from "../../../fixtures";
import PageListPage, {
  PageListPageProps
} from "../../../pages/components/PageListPage";
import { pageList } from "../../../pages/fixtures";
import Decorator from "../../Decorator";

const props: PageListPageProps = {
  ...pageListProps.default,
  pages: pageList
};

storiesOf("Views / Pages / Page list", module)
  .addDecorator(Decorator)
  .add("default", () => <PageListPage {...props} />)
  .add("loading", () => (
    <PageListPage {...props} disabled={true} pages={undefined} />
  ))
  .add("no data", () => <PageListPage {...props} pages={[]} />);
