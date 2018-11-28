import * as urlJoin from "url-join";

const siteSettingsSection = "/siteSettings";

export const siteSettingsPath = siteSettingsSection;
export const siteSettingsUrl = siteSettingsPath;

export const siteSettingsAddKeyPath = urlJoin(siteSettingsSection, "addKey");
export const siteSettingsAddKeyUrl = siteSettingsAddKeyPath;
