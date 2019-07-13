import createSvgIcon from "@material-ui/icons/utils/createSvgIcon";
import React from "react";

export const Shop = createSvgIcon(
  <>
    <rect width="24" height="24" fill="black" fillOpacity={0} />
    <rect width="20" height="19" fillOpacity={0} transform="translate(2 2)" />
    <rect width="20" height="19" fillOpacity={0} transform="translate(2 2)" />
    <rect width="20" height="19" fillOpacity={0} transform="translate(2 2)" />
    <path d="M16 6V4C16 2.89 15.11 2 14 2H10C8.89 2 8 2.89 8 4V6H2V19C2 20.11 2.89 21 4 21H20C21.11 21 22 20.11 22 19V6H16ZM10 4H14V6H10V4ZM20 19H4V8H20V19Z" />
  </>
);
Shop.displayName = "Shop";
export default Shop;
