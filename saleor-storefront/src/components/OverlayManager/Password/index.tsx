import "./scss/index.scss";

import * as React from "react";
import ReactSVG from "react-svg";

import {
  Offline,
  OfflinePlaceholder,
  Online,
  Overlay,
  OverlayContextInterface,
  PasswordResetForm
} from "../..";

import closeImg from "../../../images/x.svg";

const Password: React.FC<{ overlay: OverlayContextInterface }> = ({
  overlay,
}) => (
  <Overlay context={overlay}>
    <div className="password-reset">
      <Online>
        <div className="overlay__header">
          <p className="overlay__header-text">Reset your password</p>
          <ReactSVG
            path={closeImg}
            onClick={overlay.hide}
            className="overlay__header__close-icon"
          />
        </div>
        <div className="password-reset__content">
          <PasswordResetForm />
        </div>
      </Online>
      <Offline>
        <OfflinePlaceholder />
      </Offline>
    </div>
  </Overlay>
);

export default Password;
