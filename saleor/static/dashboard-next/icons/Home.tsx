import createSvgIcon from "@material-ui/icons/utils/createSvgIcon";
import React from "react";

export const Home = createSvgIcon(
  <>
    <rect width="24" height="24" fill="black" fillOpacity={0} />
    <rect width="20" height="17" fillOpacity={0} transform="translate(2 3)" />
    <path d="M12 5.69L17 10.19V12V18H15V14V12H13H11H9V14V18H7V12V10.19L12 5.69ZM12 3L2 12H5V20H11V14H13V20H19V12H22L12 3Z" />
  </>
);
Home.displayName = "Home";
export default Home;
