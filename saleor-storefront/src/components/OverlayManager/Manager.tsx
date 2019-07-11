import * as React from "react";

import { Overlay, OverlayContext, OverlayType } from "..";
import Cart from "./Cart";
import Login from "./Login";
import MobileNav from "./MobileNav";
import Modal from "./Modal";
import Notification from "./Notification";
import Password from "./Password";
import Search from "./Search";

const OverlayManager: React.FC = () => (
  <OverlayContext.Consumer>
    {overlay => {
      switch (overlay.type) {
        case OverlayType.modal:
          return <Modal overlay={overlay} />;

        case OverlayType.message:
          return <Notification overlay={overlay} />;

        case OverlayType.cart:
          return <Cart overlay={overlay} />;

        case OverlayType.search:
          return <Search overlay={overlay} />;

        case OverlayType.login:
          return <Login overlay={overlay} />;

        case OverlayType.register:
          return <Login overlay={overlay} active="register" />;

        case OverlayType.password:
          return <Password overlay={overlay} />;

        case OverlayType.sideNav:
          return <MobileNav overlay={overlay} />;

        case OverlayType.mainMenuNav:
          return <Overlay context={overlay} />;

        default:
          return null;
      }
    }}
  </OverlayContext.Consumer>
);

export default OverlayManager;
