import * as React from "react";

import { TypedShopInfoQuery } from "./query";
import { ShopInfo_shop } from "./types/ShopInfo";

type ShopContext = ShopInfo_shop;

export const shopContext = React.createContext<ShopContext>(undefined);

export const ShopProvider: React.StatelessComponent<{}> = ({ children }) => (
  <TypedShopInfoQuery>
    {({ data }) => (
      <shopContext.Provider value={data ? data.shop : undefined}>
        {children}
      </shopContext.Provider>
    )}
  </TypedShopInfoQuery>
);
export const Shop = shopContext.Consumer;
export default Shop;
