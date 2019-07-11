import * as React from "react";

import { maybe } from "../core/utils";

const useClickedOutside = () => {
  const [clickedOutside, setClickedOutside] = React.useState<boolean>(false);
  const elementRef = React.useRef(null);

  const handleClickOutside = (e: MouseEvent) => {
    if (maybe(() => elementRef.current && e.target, null)) {
      setClickedOutside(!elementRef.current.contains(e.target as Node));
    }
  };

  const setElementRef = () => elementRef;

  React.useEffect(() => {
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return {
    clickedOutside,
    setElementRef,
  };
};

export default useClickedOutside;
