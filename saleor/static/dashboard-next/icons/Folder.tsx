import createSvgIcon from "@material-ui/icons/utils/createSvgIcon";
import * as React from "react";

export const Folder = createSvgIcon(
  <>
    <rect width="24" height="24" fillOpacity="0" />
    <rect width="20" height="16" fillOpacity="0" transform="translate(2 4)" />
    <path d="M9.17 6L11.17 8H20V18H4V6H9.17ZM10 4H4C2.9 4 2.01 4.9 2.01 6L2 18C2 19.1 2.9 20 4 20H20C21.1 20 22 19.1 22 18V8C22 6.9 21.1 6 20 6H12L10 4Z" />
  </>
);
Folder.displayName = "Folder";
export default Folder;
