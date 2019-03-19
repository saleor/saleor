import { useContext } from "react";

import { shopContext } from "../components/Shop";

function useShop() {
  return useContext(shopContext);
}
export default useShop;
