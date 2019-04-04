import { storiesOf } from "@storybook/react";
import * as React from "react";

import { pageListProps } from "../../../fixtures";
import CountryListPage, {
  CountryListPageProps
} from "../../../taxes/components/CountryListPage";
import Decorator from "../../Decorator";
import { countries } from "./fixtures";

const props: CountryListPageProps = {
  ...pageListProps.default,
  onBack: () => undefined,
  onSubmit: () => undefined,
  onTaxFetch: () => undefined,
  shop: {
    __typename: "Shop",
    chargeTaxesOnShipping: false,
    countries,
    displayGrossPrices: true,
    includeTaxesInPrices: false
  }
};

storiesOf("Views / Taxes / Country List", module)
  .addDecorator(Decorator)
  .add("default", () => <CountryListPage {...props} />)
  .add("loading", () => (
    <CountryListPage {...props} shop={undefined} disabled={true} />
  ));
