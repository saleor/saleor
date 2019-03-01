import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";
import { Route, Switch } from "react-router-dom";

import ActionDialog from "../../../components/ActionDialog";
import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton";
import Navigator from "../../../components/Navigator";
import Shop from "../../../components/Shop";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { ShippingMethodTypeEnum } from "../../../types/globalTypes";
import ShippingZoneCountriesAssignDialog from "../../components/ShippingZoneCountriesAssignDialog";
import ShippingZoneRateDialog from "../../components/ShippingZoneRateDialog";
import { ShippingZoneDetailsFragment } from "../../types/ShippingZoneDetailsFragment";
import { shippingZoneUrl } from "../../urls";
import { ShippingZoneOperationsOutput } from "./ShippingZoneOperations";
import {
  shippingZoneAssignCountryPath,
  shippingZoneDeletePath,
  shippingZonePriceRateCreatePath,
  shippingZoneRateDeletePath,
  shippingZoneRatePath,
  shippingZoneUnassignCountryPath,
  shippingZoneWeightRateCreatePath
} from "./urls";

export interface ShippingZoneDetailsDialogsProps {
  assignCountryTransitionState: ConfirmButtonTransitionState;
  createRateTransitionState: ConfirmButtonTransitionState;
  deleteRateTransitionState: ConfirmButtonTransitionState;
  deleteZoneTransitionState: ConfirmButtonTransitionState;
  id: string;
  ops: ShippingZoneOperationsOutput;
  shippingZone: ShippingZoneDetailsFragment;
  unassignCountryTransitionState: ConfirmButtonTransitionState;
  updateRateTransitionState: ConfirmButtonTransitionState;
}

const ShippingZoneDetailsDialogs: React.StatelessComponent<
  ShippingZoneDetailsDialogsProps
> = ({
  assignCountryTransitionState,
  createRateTransitionState,
  deleteRateTransitionState,
  deleteZoneTransitionState,
  id,
  ops,
  shippingZone,
  unassignCountryTransitionState,
  updateRateTransitionState
}) => (
  <Navigator>
    {navigate => {
      const closeModal = () => navigate(shippingZoneUrl(id));
      const getShippingMethod = (methodId: string) =>
        maybe(() =>
          shippingZone.shippingMethods.find(rate => rate.id === methodId)
        );

      return (
        <Shop>
          {shop => (
            <Switch>
              <Route
                exact
                path={shippingZoneAssignCountryPath(":id")}
                render={({ match }) => (
                  <ShippingZoneCountriesAssignDialog
                    confirmButtonState={assignCountryTransitionState}
                    countries={maybe(() => shop.countries, [])}
                    initial={maybe(
                      () => shippingZone.countries.map(country => country.code),
                      []
                    )}
                    isDefault={maybe(() => shippingZone.default, false)}
                    onClose={closeModal}
                    onConfirm={formData =>
                      ops.shippingZoneUpdate.mutate({
                        id,
                        input: {
                          countries: formData.countries,
                          default: formData.restOfTheWorld
                        }
                      })
                    }
                    open={!!match}
                  />
                )}
              />
              <Route
                exact
                path={shippingZonePriceRateCreatePath(":shippingZoneId")}
                render={({ match }) => (
                  <ShippingZoneRateDialog
                    action="create"
                    confirmButtonState={createRateTransitionState}
                    defaultCurrency={maybe(() => shop.defaultCurrency)}
                    disabled={ops.shippingRateCreate.opts.loading}
                    onClose={closeModal}
                    onSubmit={formData =>
                      ops.shippingRateCreate.mutate({
                        input: {
                          maximumOrderPrice: formData.maxValue,
                          minimumOrderPrice: formData.minValue,
                          name: formData.name,
                          price: formData.isFree ? 0 : formData.price,
                          shippingZone: id,
                          type: ShippingMethodTypeEnum.PRICE
                        }
                      })
                    }
                    open={!!match}
                    rate={undefined}
                    variant={ShippingMethodTypeEnum.PRICE}
                  />
                )}
              />
              <Route
                path={shippingZoneDeletePath(":id")}
                render={({ match }) => (
                  <ActionDialog
                    confirmButtonState={deleteZoneTransitionState}
                    onClose={closeModal}
                    onConfirm={() =>
                      ops.shippingZoneDelete.mutate({
                        id
                      })
                    }
                    open={!!match}
                    title={i18n.t("Delete Shipping Zone")}
                    variant="delete"
                  >
                    <DialogContentText
                      dangerouslySetInnerHTML={{
                        __html: i18n.t(
                          "Are you sure you want to delete <strong>{{ name }}</strong>?",
                          {
                            context: "remove shipping zone",
                            name: maybe(() => shippingZone.name)
                          }
                        )
                      }}
                    />
                  </ActionDialog>
                )}
              />
              <Route
                path={shippingZoneUnassignCountryPath(":id", ":code")}
                render={({ match }) => (
                  <ActionDialog
                    confirmButtonState={unassignCountryTransitionState}
                    onClose={closeModal}
                    onConfirm={() =>
                      ops.shippingZoneUpdate.mutate({
                        id,
                        input: {
                          countries: shippingZone.countries
                            .filter(
                              country => country.code !== match.params.code
                            )
                            .map(country => country.code)
                        }
                      })
                    }
                    open={!!match}
                    title={i18n.t("Remove from shipping zone")}
                    variant="delete"
                  >
                    <DialogContentText
                      dangerouslySetInnerHTML={{
                        __html: i18n.t(
                          "Are you sure you want to remove <strong>{{ name }}</strong> from this shipping zone?",
                          {
                            context: "unassign country",
                            name: maybe(
                              () =>
                                shippingZone.countries.find(
                                  country => country.code === match.params.code
                                ).country
                            )
                          }
                        )
                      }}
                    />
                  </ActionDialog>
                )}
              />
              <Route
                path={shippingZoneRateDeletePath(":shippingZoneId", ":rateId")}
                render={({ match }) => (
                  <ActionDialog
                    confirmButtonState={deleteRateTransitionState}
                    onClose={closeModal}
                    onConfirm={() =>
                      ops.shippingRateDelete.mutate({
                        id: decodeURIComponent(match.params.rateId)
                      })
                    }
                    open={!!match}
                    title={i18n.t("Delete Shipping Method")}
                    variant="delete"
                  >
                    <DialogContentText
                      dangerouslySetInnerHTML={{
                        __html: i18n.t(
                          "Are you sure you want to delete <strong>{{ name }}</strong>?",
                          {
                            context: "remove shipping method",
                            name: maybe(
                              () =>
                                getShippingMethod(
                                  decodeURIComponent(match.params.rateId)
                                ).name
                            )
                          }
                        )
                      }}
                    />
                  </ActionDialog>
                )}
              />
              <Route
                exact
                path={shippingZoneWeightRateCreatePath(":shippingZoneId")}
                render={({ match }) => (
                  <ShippingZoneRateDialog
                    action="create"
                    confirmButtonState={createRateTransitionState}
                    defaultCurrency={maybe(() => shop.defaultCurrency)}
                    disabled={ops.shippingRateCreate.opts.loading}
                    onClose={closeModal}
                    onSubmit={formData =>
                      ops.shippingRateCreate.mutate({
                        input: {
                          maximumOrderWeight: formData.maxValue,
                          minimumOrderWeight: formData.minValue,
                          name: formData.name,
                          price: formData.isFree ? 0 : formData.price,
                          shippingZone: id,
                          type: ShippingMethodTypeEnum.WEIGHT
                        }
                      })
                    }
                    open={!!match}
                    rate={undefined}
                    variant={ShippingMethodTypeEnum.WEIGHT}
                  />
                )}
              />
              <Route
                path={shippingZoneRatePath(":shippingZoneId", ":rateId")}
                render={({ match }) => {
                  const rate = getShippingMethod(
                    decodeURIComponent(match.params.rateId)
                  );
                  return (
                    <ShippingZoneRateDialog
                      action="edit"
                      confirmButtonState={updateRateTransitionState}
                      defaultCurrency={maybe(() => shop.defaultCurrency)}
                      disabled={ops.shippingRateUpdate.opts.loading}
                      onClose={closeModal}
                      onSubmit={formData =>
                        ops.shippingRateUpdate.mutate({
                          id: decodeURIComponent(match.params.rateId),
                          input: {
                            maximumOrderPrice: formData.maxValue,
                            minimumOrderPrice: formData.minValue,
                            name: formData.name,
                            price: formData.isFree ? 0 : formData.price,
                            shippingZone: id,
                            type: maybe(() => rate.type)
                          }
                        })
                      }
                      open={!!match}
                      rate={rate}
                      variant={maybe(() => rate.type)}
                    />
                  );
                }}
              />
            </Switch>
          )}
        </Shop>
      );
    }}
  </Navigator>
);
export default ShippingZoneDetailsDialogs;
