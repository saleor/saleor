import * as React from "react";
import { Route, Switch } from "react-router-dom";

import { WindowTitle } from "../components/WindowTitle";
import i18n from "../i18n";
import { countryListPath } from "./urls";
import CountryList from "./views/CountryList";

const Component = () => (
  <>
    <WindowTitle title={i18n.t("Taxes")} />
    <Switch>
      <Route exact path={countryListPath} component={CountryList} />
    </Switch>
  </>
);

export default Component;
