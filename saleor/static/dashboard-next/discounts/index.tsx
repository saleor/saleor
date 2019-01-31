import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import { WindowTitle } from "../components/WindowTitle";
import i18n from "../i18n";
import { saleDetailsPageTab } from "./components/SaleDetailsPage";
import { saleListPath, salePath, voucherListPath } from "./urls";
import SaleDetailsViewComponent, {
  SaleDetailsQueryParams
} from "./views/SaleDetails";
import SaleListViewComponent, { SaleListQueryParams } from "./views/SaleList";
import VoucherListViewComponent, {
  VoucherListQueryParams
} from "./views/VoucherList";

const SaleListView: React.StatelessComponent<RouteComponentProps<{}>> = ({
  location
}) => {
  const qs = parseQs(location.search.substr(1));
  const params: SaleListQueryParams = {
    after: qs.after,
    before: qs.before
  };
  return <SaleListViewComponent params={params} />;
};

const SaleDetailsView: React.StatelessComponent<
  RouteComponentProps<{ id: string }>
> = ({ match, location }) => {
  const qs = parseQs(location.search.substr(1));
  const params: SaleDetailsQueryParams = {
    after: qs.after,
    before: qs.before,
    tab: saleDetailsPageTab(qs.tab)
  };
  return <SaleDetailsViewComponent id={match.params.id} params={params} />;
};

const VoucherListView: React.StatelessComponent<RouteComponentProps<{}>> = ({
  location
}) => {
  const qs = parseQs(location.search.substr(1));
  const params: VoucherListQueryParams = {
    after: qs.after,
    before: qs.before
  };
  return <VoucherListViewComponent params={params} />;
};

export const DiscountSection: React.StatelessComponent<{}> = () => (
  <>
    <WindowTitle title={i18n.t("Discounts")} />
    <Switch>
      <Route exact path={saleListPath} component={SaleListView} />
      <Route path={salePath(":id")} component={SaleDetailsView} />
      <Route exact path={voucherListPath} component={VoucherListView} />
    </Switch>
  </>
);
export default DiscountSection;
