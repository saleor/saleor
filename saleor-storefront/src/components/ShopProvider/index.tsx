import * as React from "react";

import { maybe } from "../../core/utils";
import { defaultContext, ShopContext } from "./context";
import { TypedGetShopQuery } from "./queries";

const ShopProvider: React.FC = ({ children }) => (
  <TypedGetShopQuery displayLoader={false} displayError={false}>
    {({ data }) => (
      <ShopContext.Provider value={maybe(() => data.shop, defaultContext)}>
        {children}
      </ShopContext.Provider>
    )}
  </TypedGetShopQuery>
);

export default ShopProvider;
