import * as React from "react";
import { maybe } from "../../misc";
import SiteSettingsPage from "../components/SiteSettingsPage";
import { TypedSiteSettingsQuery } from "../queries";

export const SiteSettings: React.StatelessComponent<{}> = () => (
  <TypedSiteSettingsQuery>
    {({ data, loading }) => (
      <SiteSettingsPage
        disabled={loading}
        shop={maybe(() => data.shop)}
        onKeyAdd={() => undefined}
        onKeyClick={() => undefined}
        onKeyRemove={() => undefined}
        onSubmit={() => undefined}
      />
    )}
  </TypedSiteSettingsQuery>
);
export default SiteSettings;
