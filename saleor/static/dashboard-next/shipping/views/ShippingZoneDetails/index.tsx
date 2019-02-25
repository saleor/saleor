import * as React from "react";
import { Route, Switch } from "react-router-dom";

import Messages from "../../../components/messages";
import Navigator from "../../../components/Navigator";
import Shop from "../../../components/Shop";
import { maybe } from "../../../misc";
import ShippingZoneDetailsPage from "../../components/ShippingZoneDetailsPage";
import ShippingZoneRateDialog from "../../components/ShippingZoneRateDialog";
import { TypedShippingZone } from "../../queries";
import { shippingZonesListUrl, shippingZoneUrl } from "../../urls";
import {
  shippingZonePriceRateCreatePath,
  shippingZonePriceRateCreateUrl,
  shippingZonePriceRatePath,
  shippingZonePriceRateUrl,
  shippingZoneWeightRateCreatePath,
  shippingZoneWeightRateCreateUrl,
  shippingZoneWeightRatePath,
  shippingZoneWeightRateUrl
} from "./urls";

export interface ShippingZoneDetailsProps {
  id: string;
}

const ShippingZoneDetails: React.StatelessComponent<
  ShippingZoneDetailsProps
> = ({ id }) => (
  <Navigator>
    {navigate => (
      <Messages>
        {pushMessage => (
          <Shop>
            {shop => (
              <TypedShippingZone variables={{ id }}>
                {({ data, loading }) => (
                  <>
                    <ShippingZoneDetailsPage
                      disabled={loading}
                      onBack={() => navigate(shippingZonesListUrl)}
                      onCountryAdd={() => undefined}
                      onCountryRemove={() => undefined}
                      onDelete={() => undefined}
                      onPriceRateAdd={() =>
                        navigate(shippingZonePriceRateCreateUrl(id))
                      }
                      onPriceRateEdit={rateId =>
                        navigate(shippingZonePriceRateUrl(id, rateId))
                      }
                      onRateRemove={() => undefined}
                      onSubmit={() => undefined}
                      onWeightRateAdd={() =>
                        navigate(shippingZoneWeightRateCreateUrl(id))
                      }
                      onWeightRateEdit={rateId =>
                        navigate(shippingZoneWeightRateUrl(id, rateId))
                      }
                      saveButtonBarState="default"
                      shippingZone={maybe(() => data.shippingZone)}
                    />
                    <Switch>
                      <Route
                        exact
                        path={shippingZonePriceRateCreatePath(
                          ":shippingZoneId"
                        )}
                        render={({ match }) => (
                          <ShippingZoneRateDialog
                            action="create"
                            confirmButtonState="default"
                            defaultCurrency={maybe(() => shop.defaultCurrency)}
                            disabled={loading}
                            onClose={() => navigate(shippingZoneUrl(id))}
                            onSubmit={formData => console.log(formData)}
                            open={!!match}
                            rate={undefined}
                            variant="price"
                          />
                        )}
                      />
                      <Route
                        exact
                        path={shippingZoneWeightRateCreatePath(
                          ":shippingZoneId"
                        )}
                        render={({ match }) => (
                          <ShippingZoneRateDialog
                            action="edit"
                            confirmButtonState="default"
                            defaultCurrency={maybe(() => shop.defaultCurrency)}
                            disabled={loading}
                            onClose={() => navigate(shippingZoneUrl(id))}
                            onSubmit={formData => console.log(formData)}
                            open={!!match}
                            rate={undefined}
                            variant="weight"
                          />
                        )}
                      />
                      <Route
                        path={shippingZonePriceRatePath(
                          ":shippingZoneId",
                          ":rateId"
                        )}
                        render={({ match }) => (
                          <ShippingZoneRateDialog
                            action="edit"
                            confirmButtonState="default"
                            defaultCurrency={maybe(() => shop.defaultCurrency)}
                            disabled={loading}
                            onClose={() => navigate(shippingZoneUrl(id))}
                            onSubmit={formData => console.log(formData)}
                            open={!!match}
                            rate={maybe(() =>
                              data.shippingZone.shippingMethods.find(
                                rate =>
                                  rate.id ===
                                  decodeURIComponent(match.params.rateId)
                              )
                            )}
                            variant="price"
                          />
                        )}
                      />
                      <Route
                        path={shippingZoneWeightRatePath(
                          ":shippingZoneId",
                          ":rateId"
                        )}
                        render={({ match }) => (
                          <ShippingZoneRateDialog
                            action="edit"
                            confirmButtonState="default"
                            defaultCurrency={maybe(() => shop.defaultCurrency)}
                            disabled={loading}
                            onClose={() => navigate(shippingZoneUrl(id))}
                            onSubmit={formData => console.log(formData)}
                            open={!!match}
                            rate={maybe(() =>
                              data.shippingZone.shippingMethods.find(
                                rate =>
                                  rate.id ===
                                  decodeURIComponent(match.params.rateId)
                              )
                            )}
                            variant="weight"
                          />
                        )}
                      />
                    </Switch>
                  </>
                )}
              </TypedShippingZone>
            )}
          </Shop>
        )}
      </Messages>
    )}
  </Navigator>
);
export default ShippingZoneDetails;
