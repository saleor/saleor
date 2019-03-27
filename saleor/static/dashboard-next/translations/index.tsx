import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import { WindowTitle } from "../components/WindowTitle";
import i18n from "../i18n";
import { languageEntitiesPath, languageListPath } from "./urls";
import TranslationsEntitiesComponent, {
  TranslationsEntitiesListQueryParams
} from "./views/TranslationsEntities";
import TranslationsLanguageList from "./views/TranslationsLanguageList";

type TranslationsEntitiesRouteProps = RouteComponentProps<{
  languageCode: string;
}>;
const TranslationsEntities: React.FC<TranslationsEntitiesRouteProps> = ({
  location,
  match
}) => {
  const qs = parseQs(location.search.substr(1));
  const params: TranslationsEntitiesListQueryParams = {
    after: qs.after,
    before: qs.before,
    tab: qs.tab
  };
  return (
    <TranslationsEntitiesComponent
      language={match.params.languageCode}
      params={params}
    />
  );
};

const TranslationsRouter: React.FC = () => (
  <>
    <WindowTitle title={i18n.t("Translations")} />
    <Switch>
      <Route
        exact
        path={languageListPath}
        component={TranslationsLanguageList}
      />
      <Route
        exact
        path={languageEntitiesPath(":languageCode")}
        component={TranslationsEntities}
      />
    </Switch>
  </>
);
TranslationsRouter.displayName = "TranslationsRouter";
export default TranslationsRouter;
