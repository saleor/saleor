import { storiesOf } from "@storybook/react";
import * as React from "react";

import TaxListPage, {
  TaxListPageProps
} from "../../../taxes/components/TaxListPage";
import Decorator from "../../Decorator";

const props: TaxListPageProps = {};

storiesOf("Taxes / TaxListPage", module)
  .addDecorator(Decorator)
  .add("default", () => <TaxListPage {...props} />)
  .add("loading", () => <TaxListPage {...props} taxes={undefined} />);
