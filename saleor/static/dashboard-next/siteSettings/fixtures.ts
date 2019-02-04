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
  description: "Lorem ipsum dolor sit amet",
  domain: {
    __typename: "Domain",
    host: "localhost:8000"
  },
  name: "Saleor e-commerce"
};
