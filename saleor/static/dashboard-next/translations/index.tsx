import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import { WindowTitle } from "../components/WindowTitle";
import i18n from "../i18n";
import { LanguageCodeEnum } from "../types/globalTypes";
import {
  languageEntitiesPath,
  languageEntityPath,
  languageListPath,
  TranslatableEntities
} from "./urls";
import TranslationsCategoriesComponent, {
  TranslationsCategoriesQueryParams
} from "./views/TranslationsCategories";
import TranslationsCollectionsComponent, {
  TranslationsCollectionsQueryParams
} from "./views/TranslationsCollections";
import TranslationsEntitiesComponent, {
  TranslationsEntitiesListQueryParams
} from "./views/TranslationsEntities";
import TranslationsLanguageList from "./views/TranslationsLanguageList";
import TranslationsPagesComponent, {
  TranslationsPagesQueryParams
} from "./views/TranslationsPages";
import TranslationsProductsComponent, {
  TranslationsProductsQueryParams
} from "./views/TranslationsProducts";
import TranslationsProductTypesComponent, {
  TranslationsProductTypesQueryParams
} from "./views/TranslationsProductTypes";
import TranslationsSaleComponent, {
  TranslationsSalesQueryParams
} from "./views/TranslationsSales";
import TranslationsVouchersComponent, {
  TranslationsVouchersQueryParams
} from "./views/TranslationsVouchers";

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
type TranslationsEntityRouteProps = RouteComponentProps<{
  id: string;
  languageCode: string;
}>;
const TranslationsCategories: React.FC<TranslationsEntityRouteProps> = ({
  location,
  match
}) => {
  const qs = parseQs(location.search.substr(1));
  const params: TranslationsCategoriesQueryParams = {
    activeField: qs.activeField
  };
  return (
    <TranslationsCategoriesComponent
      id={decodeURIComponent(match.params.id)}
      languageCode={LanguageCodeEnum[match.params.languageCode]}
      params={params}
    />
  );
};
const TranslationsCollections: React.FC<TranslationsEntityRouteProps> = ({
  location,
  match
}) => {
  const qs = parseQs(location.search.substr(1));
  const params: TranslationsCollectionsQueryParams = {
    activeField: qs.activeField
  };
  return (
    <TranslationsCollectionsComponent
      id={decodeURIComponent(match.params.id)}
      languageCode={LanguageCodeEnum[match.params.languageCode]}
      params={params}
    />
  );
};
const TranslationsProducts: React.FC<TranslationsEntityRouteProps> = ({
  location,
  match
}) => {
  const qs = parseQs(location.search.substr(1));
  const params: TranslationsProductsQueryParams = {
    activeField: qs.activeField
  };
  return (
    <TranslationsProductsComponent
      id={decodeURIComponent(match.params.id)}
      languageCode={LanguageCodeEnum[match.params.languageCode]}
      params={params}
    />
  );
};
const TranslationsSales: React.FC<TranslationsEntityRouteProps> = ({
  location,
  match
}) => {
  const qs = parseQs(location.search.substr(1));
  const params: TranslationsSalesQueryParams = {
    activeField: qs.activeField
  };
  return (
    <TranslationsSaleComponent
      id={decodeURIComponent(match.params.id)}
      languageCode={LanguageCodeEnum[match.params.languageCode]}
      params={params}
    />
  );
};
const TranslationsVouchers: React.FC<TranslationsEntityRouteProps> = ({
  location,
  match
}) => {
  const qs = parseQs(location.search.substr(1));
  const params: TranslationsVouchersQueryParams = {
    activeField: qs.activeField
  };
  return (
    <TranslationsVouchersComponent
      id={decodeURIComponent(match.params.id)}
      languageCode={LanguageCodeEnum[match.params.languageCode]}
      params={params}
    />
  );
};
const TranslationsPages: React.FC<TranslationsEntityRouteProps> = ({
  location,
  match
}) => {
  const qs = parseQs(location.search.substr(1));
  const params: TranslationsPagesQueryParams = {
    activeField: qs.activeField
  };
  return (
    <TranslationsPagesComponent
      id={decodeURIComponent(match.params.id)}
      languageCode={LanguageCodeEnum[match.params.languageCode]}
      params={params}
    />
  );
};
const TranslationsProductTypes: React.FC<TranslationsEntityRouteProps> = ({
  location,
  match
}) => {
  const qs = parseQs(location.search.substr(1));
  const params: TranslationsProductTypesQueryParams = {
    activeField: qs.activeField
  };
  return (
    <TranslationsProductTypesComponent
      id={decodeURIComponent(match.params.id)}
      languageCode={LanguageCodeEnum[match.params.languageCode]}
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
      <Route
        exact
        path={languageEntityPath(
          ":languageCode",
          TranslatableEntities.products,
          ":id"
        )}
        component={TranslationsProducts}
      />
      <Route
        exact
        path={languageEntityPath(
          ":languageCode",
          TranslatableEntities.categories,
          ":id"
        )}
        component={TranslationsCategories}
      />
      <Route
        exact
        path={languageEntityPath(
          ":languageCode",
          TranslatableEntities.collections,
          ":id"
        )}
        component={TranslationsCollections}
      />
      <Route
        exact
        path={languageEntityPath(
          ":languageCode",
          TranslatableEntities.sales,
          ":id"
        )}
        component={TranslationsSales}
      />
      <Route
        exact
        path={languageEntityPath(
          ":languageCode",
          TranslatableEntities.vouchers,
          ":id"
        )}
        component={TranslationsVouchers}
      />
      <Route
        exact
        path={languageEntityPath(
          ":languageCode",
          TranslatableEntities.pages,
          ":id"
        )}
        component={TranslationsPages}
      />
      <Route
        exact
        path={languageEntityPath(
          ":languageCode",
          TranslatableEntities.productTypes,
          ":id"
        )}
        component={TranslationsProductTypes}
      />
    </Switch>
  </>
);
TranslationsRouter.displayName = "TranslationsRouter";
export default TranslationsRouter;
