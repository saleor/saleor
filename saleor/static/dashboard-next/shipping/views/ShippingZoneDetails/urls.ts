import * as urlJoin from "url-join";

import { shippingZonePath } from "../../urls";

export const shippingZonePriceRatePath = (
  shippingZoneId: string,
  rateId: string
) => urlJoin(shippingZonePath(shippingZoneId), "price", rateId);
export const shippingZonePriceRateUrl = (
  shippingZoneId: string,
  rateId: string
) =>
  shippingZonePriceRatePath(
    encodeURIComponent(shippingZoneId),
    encodeURIComponent(rateId)
  );

export const shippingZoneWeightRatePath = (
  shippingZoneId: string,
  rateId: string
) => urlJoin(shippingZonePath(shippingZoneId), "weight", rateId);
export const shippingZoneWeightRateUrl = (
  shippingZoneId: string,
  rateId: string
) =>
  shippingZoneWeightRatePath(
    encodeURIComponent(shippingZoneId),
    encodeURIComponent(rateId)
  );

export const shippingZonePriceRateCreatePath = (shippingZoneId: string) =>
  urlJoin(shippingZonePath(shippingZoneId), "price", "add");
export const shippingZonePriceRateCreateUrl = (shippingZoneId: string) =>
  shippingZonePriceRateCreatePath(encodeURIComponent(shippingZoneId));

export const shippingZoneWeightRateCreatePath = (shippingZoneId: string) =>
  urlJoin(shippingZonePath(shippingZoneId), "weight", "add");
export const shippingZoneWeightRateCreateUrl = (shippingZoneId: string) =>
  shippingZoneWeightRateCreatePath(encodeURIComponent(shippingZoneId));
