import { AuthorizationKeyType } from "../types/globalTypes";
import { SiteSettings_shop } from "./types/SiteSettings";

export const shop: SiteSettings_shop = {
  __typename: "Shop",
  authorizationKeys: [
    {
      __typename: "AuthorizationKey",
      key: "n1n62jkn2123:123n",
      name: AuthorizationKeyType.FACEBOOK
    }
  ],
  companyAddress: {
    __typename: "Address",
    city: "Kenstad",
    cityArea: "Alabama",
    companyName: "Saleor e-commerce",
    country: {
      __typename: "CountryDisplay";
      code: "UA",
      country: "United Arab Emirates"
    },
    countryArea: null,
    firstName: null,
    id: "1",
    lastName: null,
    phone: "+41 876-373-9137",
    postalCode: "89880-6342",
    streetAddress1: "01419 Bernhard Plain",
    streetAddress2: null
  },
  countries: [
    {
      __typename: "CountryDisplay",
      code: "UA",
      country: "United Arab Emirates"
    }
  ],
  description: "Lorem ipsum dolor sit amet",
  domain: {
    __typename: "Domain",
    host: "localhost:8000"
  },
  name: "Saleor e-commerce"
};
