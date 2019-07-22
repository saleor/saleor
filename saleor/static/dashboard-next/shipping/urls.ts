import { stringify as stringifyQs } from "qs";
import urlJoin from "url-join";

import { BulkAction, Dialog, Pagination, SingleAction } from "../types";
import { ShippingMethodTypeEnum } from "../types/globalTypes";

export const shippingSection = "/shipping/";

export const shippingZonesListPath = shippingSection;
export type ShippingZonesListUrlDialog = "remove" | "remove-many";
export type ShippingZonesListUrlQueryParams = BulkAction &
  Dialog<ShippingZonesListUrlDialog> &
  Pagination &
  SingleAction;
export const shippingZonesListUrl = (
  params?: ShippingZonesListUrlQueryParams
) => shippingZonesListPath + "?" + stringifyQs(params);

export const shippingZonePath = (id: string) =>
  urlJoin(shippingZonesListPath, id);
export type ShippingZoneUrlDialog =
  | "add-rate"
  | "assign-country"
  | "edit-rate"
  | "remove"
  | "remove-rate"
  | "unassign-country";
export type ShippingZoneUrlQueryParams = Dialog<ShippingZoneUrlDialog> &
  SingleAction &
  Partial<{
    type: ShippingMethodTypeEnum;
  }>;
export const shippingZoneUrl = (
  id: string,
  params?: ShippingZoneUrlQueryParams
) => shippingZonePath(encodeURIComponent(id)) + "?" + stringifyQs(params);

export const shippingZoneAddPath = urlJoin(shippingZonesListPath, "add");
export const shippingZoneAddUrl = shippingZoneAddPath;
