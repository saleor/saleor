import * as React from "react";

import { maybe } from "../../misc";
import { TypedShopInfoQuery } from "./query";
import { ShopInfo_shop } from "./types/ShopInfo";

type ShopContext = ShopInfo_shop;

export const shopContext = React.createContext<ShopContext>(undefined);

export const ShopProvider: React.StatelessComponent<{}> = ({ children }) => (
  <TypedShopInfoQuery>
    {({ data }) =>
      maybe(
        () => (
          <shopContext.Provider value={data.shop}>
            {children}
          </shopContext.Provider>
        ),
        children
      )
    }
  </TypedShopInfoQuery>
);
export const Shop = shopContext.Consumer;
export default Shop;
