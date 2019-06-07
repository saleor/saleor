import { useContext } from "react";

import { shopContext } from "@saleor-components/Shop";

function useShop() {
  return useContext(shopContext);
}
export default useShop;
