import * as urlJoin from "url-join";

export const shippingSection = "/shipping/";

export const shippingZonesListPath = shippingSection;
export const shippingZonesListUrl = shippingZonesListPath;

export const shippingZonePath = (id: string) =>
  urlJoin(shippingZonesListPath, id);
export const shippingZoneUrl = (id: string) =>
  shippingZonePath(encodeURIComponent(id));

export const shippingZoneAddPath = urlJoin(shippingZonesListPath, "add");
export const shippingZoneAddUrl = shippingZoneAddPath;
