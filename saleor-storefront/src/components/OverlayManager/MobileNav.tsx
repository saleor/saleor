import * as React from "react";

import { INavItem, MobileNavList, Overlay, OverlayContextInterface } from "..";

const MobileNav: React.FC<{ overlay: OverlayContextInterface }> = ({
  overlay,
}) => {
  const items: INavItem[] = overlay.context.data;

  return (
    <Overlay context={overlay}>
      <div className="side-nav" onClick={evt => evt.stopPropagation()}>
        <MobileNavList items={items} hideOverlay={overlay.hide} />
      </div>
    </Overlay>
  );
};

export default MobileNav;
