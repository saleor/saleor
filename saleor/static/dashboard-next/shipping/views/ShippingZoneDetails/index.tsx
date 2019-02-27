import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";
import { Route, Switch } from "react-router-dom";

import ActionDialog from "../../../components/ActionDialog";
import Messages from "../../../components/messages";
import Navigator from "../../../components/Navigator";
import Shop from "../../../components/Shop";
import i18n from "../../../i18n";
import { getMutationState, maybe } from "../../../misc";
import { ShippingMethodTypeEnum } from "../../../types/globalTypes";
import ShippingZoneCountriesAssignDialog from "../../components/ShippingZoneCountriesAssignDialog";
import ShippingZoneDetailsPage from "../../components/ShippingZoneDetailsPage";
import ShippingZoneRateDialog from "../../components/ShippingZoneRateDialog";
import { TypedShippingZone } from "../../queries";
import { CreateShippingRate } from "../../types/CreateShippingRate";
import { DeleteShippingRate } from "../../types/DeleteShippingRate";
import { DeleteShippingZone } from "../../types/DeleteShippingZone";
import { UpdateShippingRate } from "../../types/UpdateShippingRate";
import { UpdateShippingZone } from "../../types/UpdateShippingZone";
import { shippingZonesListUrl, shippingZoneUrl } from "../../urls";
import ShippingZoneOperations from "./ShippingZoneOperations";
import {
  shippingZoneAssignCountryPath,
  shippingZoneAssignCountryUrl,
  shippingZoneDeletePath,
  shippingZoneDeleteUrl,
  shippingZonePriceRateCreatePath,
  shippingZonePriceRateCreateUrl,
  shippingZoneRateDeletePath,
  shippingZoneRateDeleteUrl,
  shippingZoneRatePath,
  shippingZoneRateUrl,
  shippingZoneUnassignCountryPath,
  shippingZoneUnassignCountryUrl,
  shippingZoneWeightRateCreatePath,
  shippingZoneWeightRateCreateUrl
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
            {shop => {
              const closeModal = () => navigate(shippingZoneUrl(id));

              const onShippingRateCreate = (data: CreateShippingRate) => {
                if (data.shippingPriceCreate.errors.length === 0) {
                  pushMessage({
                    text: i18n.t("Successfully created rate", {
                      context: "shipping method"
                    })
                  });
                  closeModal();
                }
              };

              const onShippingRateUpdate = (data: UpdateShippingRate) => {
                if (data.shippingPriceUpdate.errors.length === 0) {
                  pushMessage({
                    text: i18n.t("Successfully updated rate", {
                      context: "shipping method"
                    })
                  });
                  closeModal();
                }
              };

              const onShippingRateDelete = (data: DeleteShippingRate) => {
                if (data.shippingPriceDelete.errors.length === 0) {
                  pushMessage({
                    text: i18n.t("Successfully deleted rate", {
                      context: "shipping method"
                    })
                  });
                  closeModal();
                }
              };

              const onShippingZoneDelete = (data: DeleteShippingZone) => {
                if (data.shippingZoneDelete.errors.length === 0) {
                  pushMessage({
                    text: i18n.t("Successfully deleted shipping zone")
                  });
                  navigate(shippingZonesListUrl);
                }
              };

              const onShippingZoneUpdate = (data: UpdateShippingZone) => {
                if (data.shippingZoneUpdate.errors.length === 0) {
                  pushMessage({
                    text: i18n.t("Successfully updated shipping zone")
                  });
                  closeModal();
                }
              };

              return (
                <ShippingZoneOperations
                  onShippingRateCreate={onShippingRateCreate}
                  onShippingRateDelete={onShippingRateDelete}
                  onShippingRateUpdate={onShippingRateUpdate}
                  onShippingZoneDelete={onShippingZoneDelete}
                  onShippingZoneUpdate={onShippingZoneUpdate}
                >
                  {ops => (
                    <TypedShippingZone variables={{ id }}>
                      {({ data, loading }) => {
                        const formTransitionState = getMutationState(
                          ops.shippingZoneUpdate.opts.called,
                          ops.shippingZoneUpdate.opts.loading,
                          maybe(
                            () =>
                              ops.shippingZoneUpdate.opts.data
                                .shippingZoneUpdate.errors
                          )
                        );
                        const createRateTransitionState = getMutationState(
                          ops.shippingRateCreate.opts.called,
                          ops.shippingRateCreate.opts.loading,
                          maybe(
                            () =>
                              ops.shippingRateCreate.opts.data
                                .shippingPriceCreate.errors
                          )
                        );
                        const deleteRateTransitionState = getMutationState(
                          ops.shippingRateDelete.opts.called,
                          ops.shippingRateDelete.opts.loading,
                          maybe(
                            () =>
                              ops.shippingRateDelete.opts.data
                                .shippingPriceDelete.errors
                          )
                        );
                        const updateRateTransitionState = getMutationState(
                          ops.shippingRateUpdate.opts.called,
                          ops.shippingRateUpdate.opts.loading,
                          maybe(
                            () =>
                              ops.shippingRateUpdate.opts.data
                                .shippingPriceUpdate.errors
                          )
                        );
                        const deleteZoneTransitionState = getMutationState(
                          ops.shippingZoneDelete.opts.called,
                          ops.shippingZoneDelete.opts.loading,
                          maybe(
                            () =>
                              ops.shippingZoneDelete.opts.data
                                .shippingZoneDelete.errors
                          )
                        );

                        const getShippingMethod = (methodId: string) =>
                          maybe(() =>
                            data.shippingZone.shippingMethods.find(
                              rate => rate.id === methodId
                            )
                          );

                        return (
                          <>
                            <ShippingZoneDetailsPage
                              disabled={loading}
                              errors={maybe(
                                () =>
                                  ops.shippingZoneUpdate.opts.data
                                    .shippingZoneUpdate.errors
                              )}
                              onBack={() => navigate(shippingZonesListUrl)}
                              onCountryAdd={() =>
                                navigate(shippingZoneAssignCountryUrl(id))
                              }
                              onCountryRemove={code =>
                                navigate(
                                  shippingZoneUnassignCountryUrl(id, code)
                                )
                              }
                              onDelete={() =>
                                navigate(shippingZoneDeleteUrl(id))
                              }
                              onPriceRateAdd={() =>
                                navigate(shippingZonePriceRateCreateUrl(id))
                              }
                              onPriceRateEdit={rateId =>
                                navigate(shippingZoneRateUrl(id, rateId))
                              }
                              onRateRemove={rateId =>
                                navigate(shippingZoneRateDeleteUrl(id, rateId))
                              }
                              onSubmit={formData =>
                                ops.shippingZoneUpdate.mutate({
                                  id,
                                  input: {
                                    name: formData.name
                                  }
                                })
                              }
                              onWeightRateAdd={() =>
                                navigate(shippingZoneWeightRateCreateUrl(id))
                              }
                              onWeightRateEdit={rateId =>
                                navigate(shippingZoneRateUrl(id, rateId))
                              }
                              saveButtonBarState={formTransitionState}
                              shippingZone={maybe(() => data.shippingZone)}
                            />
                            <Switch>
                              <Route
                                exact
                                path={shippingZoneAssignCountryPath(":id")}
                                render={({ match }) => (
                                  <ShippingZoneCountriesAssignDialog
                                    confirmButtonState={formTransitionState}
                                    countries={maybe(() => shop.countries, [])}
                                    initial={maybe(
                                      () =>
                                        data.shippingZone.countries.map(
                                          country => country.code
                                        ),
                                      []
                                    )}
                                    isDefault={maybe(
                                      () => data.shippingZone.default,
                                      false
                                    )}
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
                                path={shippingZonePriceRateCreatePath(
                                  ":shippingZoneId"
                                )}
                                render={({ match }) => (
                                  <ShippingZoneRateDialog
                                    action="create"
                                    confirmButtonState={
                                      createRateTransitionState
                                    }
                                    defaultCurrency={maybe(
                                      () => shop.defaultCurrency
                                    )}
                                    disabled={
                                      ops.shippingRateCreate.opts.loading
                                    }
                                    onClose={closeModal}
                                    onSubmit={formData =>
                                      ops.shippingRateCreate.mutate({
                                        input: {
                                          maximumOrderPrice: formData.maxValue,
                                          minimumOrderPrice: formData.minValue,
                                          name: formData.name,
                                          price: formData.isFree
                                            ? 0
                                            : formData.price,
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
                                    confirmButtonState={
                                      deleteZoneTransitionState
                                    }
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
                                            name: maybe(
                                              () => data.shippingZone.name
                                            )
                                          }
                                        )
                                      }}
                                    />
                                  </ActionDialog>
                                )}
                              />
                              <Route
                                path={shippingZoneUnassignCountryPath(
                                  ":id",
                                  ":code"
                                )}
                                render={({ match }) => (
                                  <ActionDialog
                                    confirmButtonState={formTransitionState}
                                    onClose={closeModal}
                                    onConfirm={() =>
                                      ops.shippingZoneUpdate.mutate({
                                        id,
                                        input: {
                                          countries: data.shippingZone.countries
                                            .filter(
                                              country =>
                                                country.code !==
                                                match.params.code
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
                                                data.shippingZone.countries.find(
                                                  country =>
                                                    country.code ===
                                                    match.params.code
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
                                path={shippingZoneRateDeletePath(
                                  ":shippingZoneId",
                                  ":rateId"
                                )}
                                render={({ match }) => (
                                  <ActionDialog
                                    confirmButtonState={
                                      deleteRateTransitionState
                                    }
                                    onClose={closeModal}
                                    onConfirm={() =>
                                      ops.shippingRateDelete.mutate({
                                        id: decodeURIComponent(
                                          match.params.rateId
                                        )
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
                                                  decodeURIComponent(
                                                    match.params.rateId
                                                  )
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
                                path={shippingZoneWeightRateCreatePath(
                                  ":shippingZoneId"
                                )}
                                render={({ match }) => (
                                  <ShippingZoneRateDialog
                                    action="create"
                                    confirmButtonState={
                                      createRateTransitionState
                                    }
                                    defaultCurrency={maybe(
                                      () => shop.defaultCurrency
                                    )}
                                    disabled={
                                      ops.shippingRateCreate.opts.loading
                                    }
                                    onClose={closeModal}
                                    onSubmit={formData =>
                                      ops.shippingRateCreate.mutate({
                                        input: {
                                          maximumOrderWeight: formData.maxValue,
                                          minimumOrderWeight: formData.minValue,
                                          name: formData.name,
                                          price: formData.isFree
                                            ? 0
                                            : formData.price,
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
                                path={shippingZoneRatePath(
                                  ":shippingZoneId",
                                  ":rateId"
                                )}
                                render={({ match }) => {
                                  const rate = getShippingMethod(
                                    decodeURIComponent(match.params.rateId)
                                  );
                                  return (
                                    <ShippingZoneRateDialog
                                      action="edit"
                                      confirmButtonState={
                                        updateRateTransitionState
                                      }
                                      defaultCurrency={maybe(
                                        () => shop.defaultCurrency
                                      )}
                                      disabled={
                                        ops.shippingRateUpdate.opts.loading
                                      }
                                      onClose={closeModal}
                                      onSubmit={formData =>
                                        ops.shippingRateUpdate.mutate({
                                          id: decodeURIComponent(
                                            match.params.rateId
                                          ),
                                          input: {
                                            maximumOrderPrice:
                                              formData.maxValue,
                                            minimumOrderPrice:
                                              formData.minValue,
                                            name: formData.name,
                                            price: formData.isFree
                                              ? 0
                                              : formData.price,
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
                          </>
                        );
                      }}
                    </TypedShippingZone>
                  )}
                </ShippingZoneOperations>
              );
            }}
          </Shop>
        )}
      </Messages>
    )}
  </Navigator>
);
export default ShippingZoneDetails;
