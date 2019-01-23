import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import { WindowTitle } from "../components/WindowTitle";
import i18n from "../i18n";
import { saleListPath, voucherListPath } from "./urls";
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
      <Route exact path={voucherListPath} component={VoucherListView} />
    </Switch>
  </>
);
export default DiscountSection;
