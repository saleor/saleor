// tslint:disable:no-submodule-imports
import * as throttle from "lodash/throttle";
import { useEffect, useState } from "react";

function getPosition() {
  return {
    x: window.pageXOffset,
    y: window.pageYOffset
  };
}

function useScroll() {
  const [scroll, setScroll] = useState(getPosition);

  useEffect(() => {
    const handleScroll = throttle(() => setScroll(getPosition()), 250);

    window.addEventListener("scroll", handleScroll);

    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return scroll;
}
export default useScroll;
