import { stringify as stringifyQs } from "qs";

import { Dialog } from "../types";

const siteSettingsSection = "/site-settings";

export const siteSettingsPath = siteSettingsSection;
export type SiteSettingsUrlDialog = "add-key";
export type SiteSettingsUrlQueryParams = Dialog<SiteSettingsUrlDialog>;
export const siteSettingsUrl = (params?: SiteSettingsUrlQueryParams) =>
  siteSettingsPath + "?" + stringifyQs(params);
