import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import { WindowTitle } from "../components/WindowTitle";
import i18n from "../i18n";
import { shippingZonePath, shippingZonesListPath } from "./urls";
import ShippingZoneDetailsComponent from "./views/ShippingZoneDetails";
import ShippingZonesListComponent, {
  ShippingZonesListQueryParams
} from "./views/ShippingZonesList";

const ShippingZonesList: React.StatelessComponent<RouteComponentProps<{}>> = ({
  location
}) => {
  const qs = parseQs(location.search.substr(1));
  const params: ShippingZonesListQueryParams = {
    after: qs.after,
    before: qs.before,
    delete: qs.delete
  };
  return <ShippingZonesListComponent params={params} />;
};

interface ShippingZoneDetailsRouteProps {
  id: string;
}
const ShippingZoneDetails: React.StatelessComponent<
  RouteComponentProps<ShippingZoneDetailsRouteProps>
> = ({ match }) => (
  <ShippingZoneDetailsComponent id={decodeURIComponent(match.params.id)} />
);

export const ShippingRouter: React.StatelessComponent = () => (
  <>
    <WindowTitle title={i18n.t("Shipping")} />
    <Switch>
      <Route exact path={shippingZonesListPath} component={ShippingZonesList} />
      <Route path={shippingZonePath(":id")} component={ShippingZoneDetails} />
    </Switch>
  </>
);
export default ShippingRouter;
