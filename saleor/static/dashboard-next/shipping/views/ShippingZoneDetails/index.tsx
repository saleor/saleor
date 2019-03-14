import * as React from "react";

import Messages from "../../../components/messages";
import Navigator from "../../../components/Navigator";
import i18n from "../../../i18n";
import { getMutationState, maybe } from "../../../misc";
import ShippingZoneDetailsPage from "../../components/ShippingZoneDetailsPage";
import { TypedShippingZone } from "../../queries";
import { CreateShippingRate } from "../../types/CreateShippingRate";
import { DeleteShippingRate } from "../../types/DeleteShippingRate";
import { DeleteShippingZone } from "../../types/DeleteShippingZone";
import { UpdateShippingRate } from "../../types/UpdateShippingRate";
import { UpdateShippingZone } from "../../types/UpdateShippingZone";
import { shippingZonesListUrl, shippingZoneUrl } from "../../urls";
import ShippingZoneDetailsDialogs from "./ShippingZoneDetailsDialogs";
import ShippingZoneOperations from "./ShippingZoneOperations";
import {
  shippingZoneAssignCountryUrl,
  shippingZoneDeleteUrl,
  shippingZonePriceRateCreateUrl,
  shippingZoneRateDeleteUrl,
  shippingZoneRateUrl,
  shippingZoneUnassignCountryUrl,
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
        {pushMessage => {
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
                          ops.shippingZoneUpdate.opts.data.shippingZoneUpdate
                            .errors
                      )
                    );
                    const createRateTransitionState = getMutationState(
                      ops.shippingRateCreate.opts.called,
                      ops.shippingRateCreate.opts.loading,
                      maybe(
                        () =>
                          ops.shippingRateCreate.opts.data.shippingPriceCreate
                            .errors
                      )
                    );
                    const deleteRateTransitionState = getMutationState(
                      ops.shippingRateDelete.opts.called,
                      ops.shippingRateDelete.opts.loading,
                      maybe(
                        () =>
                          ops.shippingRateDelete.opts.data.shippingPriceDelete
                            .errors
                      )
                    );
                    const updateRateTransitionState = getMutationState(
                      ops.shippingRateUpdate.opts.called,
                      ops.shippingRateUpdate.opts.loading,
                      maybe(
                        () =>
                          ops.shippingRateUpdate.opts.data.shippingPriceUpdate
                            .errors
                      )
                    );
                    const deleteZoneTransitionState = getMutationState(
                      ops.shippingZoneDelete.opts.called,
                      ops.shippingZoneDelete.opts.loading,
                      maybe(
                        () =>
                          ops.shippingZoneDelete.opts.data.shippingZoneDelete
                            .errors
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
                            navigate(shippingZoneUnassignCountryUrl(id, code))
                          }
                          onDelete={() => navigate(shippingZoneDeleteUrl(id))}
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
                        <ShippingZoneDetailsDialogs
                          assignCountryTransitionState={formTransitionState}
                          createRateTransitionState={createRateTransitionState}
                          deleteRateTransitionState={deleteRateTransitionState}
                          deleteZoneTransitionState={deleteZoneTransitionState}
                          id={id}
                          ops={ops}
                          shippingZone={data.shippingZone}
                          unassignCountryTransitionState={formTransitionState}
                          updateRateTransitionState={updateRateTransitionState}
                        />
                      </>
                    );
                  }}
                </TypedShippingZone>
              )}
            </ShippingZoneOperations>
          );
        }}
      </Messages>
    )}
  </Navigator>
);
export default ShippingZoneDetails;
