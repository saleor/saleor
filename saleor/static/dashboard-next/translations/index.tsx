import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import { WindowTitle } from "../components/WindowTitle";
import i18n from "../i18n";
import { languageListPath } from "./urls";
import TranslationsLanguageList from "./views/TranslationsLanguageList";

const TranslationsRouter: React.FC = () => (
  <>
    <WindowTitle title={i18n.t("Translations")} />
    <Switch>
      <Route
        exact
        path={languageListPath}
        component={TranslationsLanguageList}
      />
    </Switch>
  </>
);
TranslationsRouter.displayName = "TranslationsRouter";
export default TranslationsRouter;
