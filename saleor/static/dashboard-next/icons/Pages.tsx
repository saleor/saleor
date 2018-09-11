import createSvgIcon from "@material-ui/icons/utils/createSvgIcon";
import * as React from "react";

export const Pages = createSvgIcon(
  <>
    <rect width="24" height="24" fillOpacity="0" />
    <rect width="18" height="18" fillOpacity="0" transform="translate(3 3)" />
    <path d="M19 3H5C3.9 3 3 3.9 3 5V19C3 20.1 3.9 21 5 21H19C20.1 21 21 20.1 21 19V12V5C21 3.9 20.1 3 19 3ZM13 5H19V11H16L17 7L13 8V5ZM5 5H11V8L7 7L8 11H5V5ZM11 19H5V13H8L7 17L11 16V19ZM19 19H13V16L17 17L16 13H19V19ZM14.63 14.63L12 13.72L9.37 14.63L10.28 12L9.37 9.37L12 10.28L14.63 9.37L13.72 12L14.63 14.63Z" />
  </>
);
Pages.displayName = "Pages";
export default Pages;
