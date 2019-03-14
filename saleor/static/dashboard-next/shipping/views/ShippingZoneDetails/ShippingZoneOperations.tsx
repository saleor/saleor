import * as React from "react";

import { getMutationProviderData } from "../../../misc";
import { PartialMutationProviderOutput } from "../../../types";
import {
  TypedCreateShippingRate,
  TypedDeleteShippingRate,
  TypedDeleteShippingZone,
  TypedUpdateShippingRate,
  TypedUpdateShippingZone
} from "../../mutations";
import {
  CreateShippingRate,
  CreateShippingRateVariables
} from "../../types/CreateShippingRate";
import {
  DeleteShippingRate,
  DeleteShippingRateVariables
} from "../../types/DeleteShippingRate";
import {
  DeleteShippingZone,
  DeleteShippingZoneVariables
} from "../../types/DeleteShippingZone";
import {
  UpdateShippingRate,
  UpdateShippingRateVariables
} from "../../types/UpdateShippingRate";
import {
  UpdateShippingZone,
  UpdateShippingZoneVariables
} from "../../types/UpdateShippingZone";

export interface ShippingZoneOperationsOutput {
  shippingRateCreate: PartialMutationProviderOutput<
    CreateShippingRate,
    CreateShippingRateVariables
  >;
  shippingRateDelete: PartialMutationProviderOutput<
    DeleteShippingRate,
    DeleteShippingRateVariables
  >;
  shippingRateUpdate: PartialMutationProviderOutput<
    UpdateShippingRate,
    UpdateShippingRateVariables
  >;
  shippingZoneDelete: PartialMutationProviderOutput<
    DeleteShippingZone,
    DeleteShippingZoneVariables
  >;
  shippingZoneUpdate: PartialMutationProviderOutput<
    UpdateShippingZone,
    UpdateShippingZoneVariables
  >;
}
interface ShippingZoneOperationsProps {
  children: (props: ShippingZoneOperationsOutput) => React.ReactNode;
  onShippingRateCreate: (data: CreateShippingRate) => void;
  onShippingRateDelete: (data: DeleteShippingRate) => void;
  onShippingRateUpdate: (data: UpdateShippingRate) => void;
  onShippingZoneDelete: (data: DeleteShippingZone) => void;
  onShippingZoneUpdate: (data: UpdateShippingZone) => void;
}

const ShippingZoneOperations: React.StatelessComponent<
  ShippingZoneOperationsProps
> = ({
  children,
  onShippingRateCreate,
  onShippingRateDelete,
  onShippingRateUpdate,
  onShippingZoneDelete,
  onShippingZoneUpdate
}) => (
  <TypedCreateShippingRate onCompleted={onShippingRateCreate}>
    {(...shippingRateCreate) => (
      <TypedDeleteShippingRate onCompleted={onShippingRateDelete}>
        {(...shippingRateDelete) => (
          <TypedUpdateShippingRate onCompleted={onShippingRateUpdate}>
            {(...shippingRateUpdate) => (
              <TypedDeleteShippingZone onCompleted={onShippingZoneDelete}>
                {(...shippingZoneDelete) => (
                  <TypedUpdateShippingZone onCompleted={onShippingZoneUpdate}>
                    {(...shippingZoneUpdate) =>
                      children({
                        shippingRateCreate: getMutationProviderData(
                          ...shippingRateCreate
                        ),
                        shippingRateDelete: getMutationProviderData(
                          ...shippingRateDelete
                        ),
                        shippingRateUpdate: getMutationProviderData(
                          ...shippingRateUpdate
                        ),
                        shippingZoneDelete: getMutationProviderData(
                          ...shippingZoneDelete
                        ),
                        shippingZoneUpdate: getMutationProviderData(
                          ...shippingZoneUpdate
                        )
                      })
                    }
                  </TypedUpdateShippingZone>
                )}
              </TypedDeleteShippingZone>
            )}
          </TypedUpdateShippingRate>
        )}
      </TypedDeleteShippingRate>
    )}
  </TypedCreateShippingRate>
);
ShippingZoneOperations.displayName = "ShippingZoneOperations";
export default ShippingZoneOperations;
