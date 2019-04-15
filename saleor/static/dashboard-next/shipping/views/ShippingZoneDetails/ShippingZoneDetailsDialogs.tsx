import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";

import ActionDialog from "../../../components/ActionDialog";
import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton";
import useNavigator from "../../../hooks/useNavigator";
import useShop from "../../../hooks/useShop";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { ShippingMethodTypeEnum } from "../../../types/globalTypes";
import ShippingZoneCountriesAssignDialog from "../../components/ShippingZoneCountriesAssignDialog";
import ShippingZoneRateDialog from "../../components/ShippingZoneRateDialog";
import { ShippingZoneDetailsFragment } from "../../types/ShippingZoneDetailsFragment";
import { shippingZoneUrl, ShippingZoneUrlQueryParams } from "../../urls";
import { ShippingZoneOperationsOutput } from "./ShippingZoneOperations";

export interface ShippingZoneDetailsDialogsProps {
  assignCountryTransitionState: ConfirmButtonTransitionState;
  createRateTransitionState: ConfirmButtonTransitionState;
  deleteRateTransitionState: ConfirmButtonTransitionState;
  deleteZoneTransitionState: ConfirmButtonTransitionState;
  id: string;
  ops: ShippingZoneOperationsOutput;
  params: ShippingZoneUrlQueryParams;
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
  params,
  shippingZone,
  unassignCountryTransitionState,
  updateRateTransitionState
}) => {
  const navigate = useNavigator();
  const shop = useShop();

  const closeModal = () => navigate(shippingZoneUrl(id), true);

  const rate = maybe(() =>
    shippingZone.shippingMethods.find(rate => rate.id === params.id)
  );

  return (
    <>
      <ShippingZoneRateDialog
        action="edit"
        confirmButtonState={updateRateTransitionState}
        defaultCurrency={maybe(() => shop.defaultCurrency)}
        disabled={ops.shippingRateUpdate.opts.loading}
        errors={maybe(
          () => ops.shippingRateUpdate.opts.data.shippingPriceUpdate.errors,
          []
        )}
        onClose={closeModal}
        onSubmit={formData =>
          ops.shippingRateUpdate.mutate({
            id: params.id,
            input: {
              maximumOrderPrice: formData.noLimits
                ? null
                : parseFloat(formData.maxValue),
              minimumOrderPrice: formData.noLimits
                ? null
                : parseFloat(formData.minValue),
              name: formData.name,
              price: formData.isFree ? 0 : parseFloat(formData.price),
              shippingZone: id,
              type: maybe(() => rate.type)
            }
          })
        }
        open={params.action === "edit-rate"}
        rate={rate}
        variant={maybe(() => rate.type)}
      />
      <ActionDialog
        confirmButtonState={deleteRateTransitionState}
        onClose={closeModal}
        onConfirm={() =>
          ops.shippingRateDelete.mutate({
            id: params.id
          })
        }
        open={params.action === "remove-rate"}
        title={i18n.t("Delete Shipping Method")}
        variant="delete"
      >
        <DialogContentText
          dangerouslySetInnerHTML={{
            __html: i18n.t(
              "Are you sure you want to delete <strong>{{ name }}</strong>?",
              {
                context: "remove shipping method",
                name: maybe(() => rate.name, "...")
              }
            )
          }}
        />
      </ActionDialog>
      <ShippingZoneRateDialog
        action="create"
        confirmButtonState={createRateTransitionState}
        defaultCurrency={maybe(() => shop.defaultCurrency)}
        disabled={ops.shippingRateCreate.opts.loading}
        errors={maybe(
          () => ops.shippingRateCreate.opts.data.shippingPriceCreate.errors,
          []
        )}
        onClose={closeModal}
        onSubmit={formData =>
          ops.shippingRateCreate.mutate({
            input: {
              maximumOrderPrice:
                params.type === ShippingMethodTypeEnum.PRICE
                  ? formData.noLimits
                    ? null
                    : parseFloat(formData.maxValue)
                  : null,
              maximumOrderWeight:
                params.type === ShippingMethodTypeEnum.WEIGHT
                  ? formData.noLimits
                    ? null
                    : parseFloat(formData.maxValue)
                  : null,

              minimumOrderPrice:
                params.type === ShippingMethodTypeEnum.PRICE
                  ? formData.noLimits
                    ? null
                    : parseFloat(formData.minValue)
                  : null,
              minimumOrderWeight:
                params.type === ShippingMethodTypeEnum.WEIGHT
                  ? formData.noLimits
                    ? null
                    : parseFloat(formData.minValue)
                  : null,
              name: formData.name,
              price: formData.isFree ? 0 : parseFloat(formData.price),
              shippingZone: id,
              type: ShippingMethodTypeEnum.PRICE
            }
          })
        }
        open={params.action === "add-rate"}
        rate={undefined}
        variant={params.type}
      />
      <ActionDialog
        confirmButtonState={deleteZoneTransitionState}
        onClose={closeModal}
        onConfirm={() =>
          ops.shippingZoneDelete.mutate({
            id
          })
        }
        open={params.action === "remove"}
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
        open={params.action === "assign-country"}
      />
      <ActionDialog
        confirmButtonState={unassignCountryTransitionState}
        onClose={closeModal}
        onConfirm={() =>
          ops.shippingZoneUpdate.mutate({
            id,
            input: {
              countries: shippingZone.countries
                .filter(country => country.code !== params.id)
                .map(country => country.code)
            }
          })
        }
        open={params.action === "unassign-country"}
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
                      country => country.code === params.id
                    ).country
                )
              }
            )
          }}
        />
      </ActionDialog>
    </>
  );
};
export default ShippingZoneDetailsDialogs;
