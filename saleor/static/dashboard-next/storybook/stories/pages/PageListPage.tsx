import { storiesOf } from "@storybook/react";
import * as React from "react";

import { pageListProps } from "../../../fixtures";
import PageList from "../../../pages/components/PageListPage";
import { pages } from "../../../pages/fixtures";
import { Decorator } from "../../Decorator";

storiesOf("Views / Pages / Page list", module)
  .addDecorator(Decorator)
  .add("default", () => <PageList pages={pages} {...pageListProps.default} />)
  .add("loading", () => <PageList {...pageListProps.loading} />)
  .add("no data", () => <PageList pages={[]} {...pageListProps.default} />);
