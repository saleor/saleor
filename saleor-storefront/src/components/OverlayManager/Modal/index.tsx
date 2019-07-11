import "./scss/index.scss";

import * as React from "react";

import { Overlay, OverlayContextInterface } from "../..";

const Modal: React.FC<{ overlay: OverlayContextInterface }> = ({
  overlay,
}) => <Overlay context={overlay}>{overlay.context.content}</Overlay>;

export default Modal;
