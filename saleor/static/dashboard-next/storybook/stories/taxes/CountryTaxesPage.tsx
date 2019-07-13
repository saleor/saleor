import { storiesOf } from "@storybook/react";
import React from "react";

import CountryTaxesPage, {
  CountryTaxesPageProps
} from "../../../taxes/components/CountryTaxesPage";
import Decorator from "../../Decorator";
import { countries } from "./fixtures";

const props: CountryTaxesPageProps = {
  countryName: "Austria",
  onBack: () => undefined,
  taxCategories: countries[0].vat.reducedRates
};

storiesOf("Views / Taxes / Reduced Tax Categories", module)
  .addDecorator(Decorator)
  .add("default", () => <CountryTaxesPage {...props} />)
  .add("loading", () => (
    <CountryTaxesPage
      {...props}
      countryName={undefined}
      taxCategories={undefined}
    />
  ));
