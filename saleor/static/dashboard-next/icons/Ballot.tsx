import createSvgIcon from "@material-ui/icons/utils/createSvgIcon";
import React from "react";

export const Ballot = createSvgIcon(
  <>
    <rect width="24" height="24" fill="black" fillOpacity="0" />
    <rect width="18" height="18" fillOpacity="0" transform="translate(3 3)" />
    <rect width="18" fill="black" fillOpacity="0" transform="translate(3 3)" />
    <path d="M18 7.5H13V9.5H18V7.5Z" />
    <path d="M18 14.5H13V16.5H18V14.5Z" />
    <path d="M19 3H5C3.9 3 3 3.9 3 5V19C3 20.1 3.9 21 5 21H19C20.1 21 21 20.1 21 19V5C21 3.9 20.1 3 19 3ZM19 19H5V5H19V19Z" />
    <path d="M11 6H6V11H11V6ZM10 10H7V7H10V10Z" />
    <path d="M11 13H6V18H11V13ZM10 17H7V14H10V17Z" />
  </>
);
Ballot.displayName = "Ballot";
export default Ballot;
