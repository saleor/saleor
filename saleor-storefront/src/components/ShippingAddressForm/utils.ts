import { maybe } from "../../core/utils";
import {
  getShop_shop_defaultCountry,
  getShop_shop_geolocalization
} from "../ShopProvider/types/getShop";
import { FormAddressType } from "./types";

export const getFormData = (
  geolocalization: getShop_shop_geolocalization | null,
  defaultCountry: getShop_shop_defaultCountry | null,
  data?: FormAddressType
) =>
  data || {
    country: {
      code: maybe(() => geolocalization.country.code, defaultCountry.code),
      country: maybe(
        () => geolocalization.country.country,
        defaultCountry.country
      ),
    },
  };
