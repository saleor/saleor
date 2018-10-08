import gql from "graphql-tag";
import { TypedQuery } from "../queries";
import { SiteSettings } from "./types/SiteSettings";

export const shopFragment = gql`
  fragment ShopFragment on Shop {
    authorizationKeys {
      key
      name
    }
    description
    domain {
      host
    }
    name
  }
`;
const siteSettings = gql`
  ${shopFragment}
  query SiteSettings {
    shop {
      ...ShopFragment
    }
  }
`;
export const TypedSiteSettingsQuery = TypedQuery<SiteSettings, {}>(
  siteSettings
);
