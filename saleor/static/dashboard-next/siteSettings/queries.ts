import gql from "graphql-tag";
import { fragmentAddress } from "../orders/queries";
import { TypedQuery } from "../queries";
import { SiteSettings } from "./types/SiteSettings";

export const shopFragment = gql`
  ${fragmentAddress}
  fragment ShopFragment on Shop {
    authorizationKeys {
      key
      name
    }
    companyAddress {
      ...AddressFragment
    }
    countries {
      code
      country
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
