import { createContext } from "react";

import { getShop_shop } from "./types/getShop";

export const defaultCountry = {
  __typename: "CountryDisplay" as "CountryDisplay",
  code: "US",
  country: "United States of America",
};

export const defaultContext: getShop_shop = {
  __typename: "Shop",
  countries: [],
  defaultCountry,
  geolocalization: { __typename: "Geolocalization", country: defaultCountry },
};

export const ShopContext = createContext<getShop_shop>(defaultContext);

ShopContext.displayName = "ShopContext";
