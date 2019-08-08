import throttle from "lodash-es/throttle";
import { useEffect, useState } from "react";

function getPosition() {
  return {
    x: window.pageXOffset,
    y: window.pageYOffset
  };
}

function useWindowScroll() {
  const [scroll, setScroll] = useState(getPosition);

  useEffect(() => {
    const handleScroll = throttle(() => setScroll(getPosition()), 100);

    window.addEventListener("scroll", handleScroll);

    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return scroll;
}
export default useWindowScroll;
