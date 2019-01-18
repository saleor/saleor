import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import { WindowTitle } from "../components/WindowTitle";
import i18n from "../i18n";
import { countryListPath, countryTaxRatesPath } from "./urls";
import CountryList from "./views/CountryList";
import CountryTaxesComponent, {
  CountryTaxesParams
} from "./views/CountryTaxes";

const CountryTaxes: React.StatelessComponent<
  RouteComponentProps<CountryTaxesParams>
> = ({ match }) => <CountryTaxesComponent code={match.params.code} />;

const Component = () => (
  <>
    <WindowTitle title={i18n.t("Taxes")} />
    <Switch>
      <Route exact path={countryListPath} component={CountryList} />
      <Route
        exact
        path={countryTaxRatesPath(":code")}
        component={CountryTaxes}
      />
    </Switch>
  </>
);

export default Component;
