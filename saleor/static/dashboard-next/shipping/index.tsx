import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import { WindowTitle } from "../components/WindowTitle";
import i18n from "../i18n";
import {
  shippingZoneAddPath,
  shippingZonePath,
  shippingZonesListPath,
  ShippingZonesListUrlQueryParams,
  ShippingZoneUrlQueryParams
} from "./urls";
import ShippingZoneCreate from "./views/ShippingZoneCreate";
import ShippingZoneDetailsComponent from "./views/ShippingZoneDetails";
import ShippingZonesListComponent from "./views/ShippingZonesList";

const ShippingZonesList: React.StatelessComponent<RouteComponentProps<{}>> = ({
  location
}) => {
  const qs = parseQs(location.search.substr(1));
  const params: ShippingZonesListUrlQueryParams = qs;
  return <ShippingZonesListComponent params={params} />;
};

interface ShippingZoneDetailsRouteProps {
  id: string;
}
const ShippingZoneDetails: React.StatelessComponent<
  RouteComponentProps<ShippingZoneDetailsRouteProps>
> = ({ location, match }) => {
  const qs = parseQs(location.search.substr(1));
  const params: ShippingZoneUrlQueryParams = qs;
  return (
    <ShippingZoneDetailsComponent
      id={decodeURIComponent(match.params.id)}
      params={params}
    />
  );
};

export const ShippingRouter: React.StatelessComponent = () => (
  <>
    <WindowTitle title={i18n.t("Shipping")} />
    <Switch>
      <Route exact path={shippingZonesListPath} component={ShippingZonesList} />
      <Route exact path={shippingZoneAddPath} component={ShippingZoneCreate} />
      <Route path={shippingZonePath(":id")} component={ShippingZoneDetails} />
    </Switch>
  </>
);
export default ShippingRouter;
