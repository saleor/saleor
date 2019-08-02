import throttle from "lodash-es/throttle";
import { MutableRefObject, useEffect, useState } from "react";

function getPosition(anchor?: HTMLElement) {
  if (!!anchor) {
    return {
      x: anchor.scrollLeft,
      y: anchor.scrollTop
    };
  }
  return {
    x: 0,
    y: 0
  };
}

function useElementScroll(anchor: MutableRefObject<HTMLElement>) {
  const [scroll, setScroll] = useState(getPosition(anchor.current));

  useEffect(() => {
    if (!!anchor.current) {
      const handleScroll = throttle(
        () => setScroll(getPosition(anchor.current)),
        100
      );
      anchor.current.addEventListener("scroll", handleScroll);

      return () => anchor.current.removeEventListener("scroll", handleScroll);
    }
  }, [anchor.current]);

  return scroll;
}
export default useElementScroll;
