import * as urlJoin from "url-join";

import { shippingZonePath } from "../../urls";

export const shippingZoneRatePath = (shippingZoneId: string, rateId: string) =>
  urlJoin(shippingZonePath(shippingZoneId), rateId);
export const shippingZoneRateUrl = (shippingZoneId: string, rateId: string) =>
  shippingZoneRatePath(
    encodeURIComponent(shippingZoneId),
    encodeURIComponent(rateId)
  );

export const shippingZonePriceRateCreatePath = (shippingZoneId: string) =>
  urlJoin(shippingZonePath(shippingZoneId), "add", "price");
export const shippingZonePriceRateCreateUrl = (shippingZoneId: string) =>
  shippingZonePriceRateCreatePath(encodeURIComponent(shippingZoneId));

export const shippingZoneWeightRateCreatePath = (shippingZoneId: string) =>
  urlJoin(shippingZonePath(shippingZoneId), "add", "weight");
export const shippingZoneWeightRateCreateUrl = (shippingZoneId: string) =>
  shippingZoneWeightRateCreatePath(encodeURIComponent(shippingZoneId));

export const shippingZoneRateDeletePath = (
  shippingZoneId: string,
  rateId: string
) => urlJoin(shippingZonePath(shippingZoneId), rateId, "delete");
export const shippingZoneRateDeleteUrl = (
  shippingZoneId: string,
  rateId: string
) =>
  shippingZoneRateDeletePath(
    encodeURIComponent(shippingZoneId),
    encodeURIComponent(rateId)
  );

export const shippingZoneDeletePath = (id: string) =>
  urlJoin(shippingZonePath(id), "delete");
export const shippingZoneDeleteUrl = (id: string) =>
  shippingZoneDeletePath(encodeURIComponent(id));

export const shippingZoneAssignCountryPath = (id: string) =>
  urlJoin(shippingZonePath(id), "assign-countries");
export const shippingZoneAssignCountryUrl = (id: string) =>
  shippingZoneAssignCountryPath(encodeURIComponent(id));

export const shippingZoneUnassignCountryPath = (id: string, code: string) =>
  urlJoin(shippingZonePath(id), "unassign-country", code);
export const shippingZoneUnassignCountryUrl = (id: string, code: string) =>
  shippingZoneUnassignCountryPath(encodeURIComponent(id), code);
