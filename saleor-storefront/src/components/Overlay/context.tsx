import * as React from "react";

export enum OverlayType {
  cart = "cart",
  checkout = "checkout",
  login = "login",
  message = "message",
  sideNav = "side-nav",
  password = "password",
  search = "search",
  mainMenuNav = "main-menu-nav",
  modal = "modal",
  register = "register",
}

export enum OverlayTheme {
  left = "left",
  right = "right",
  modal = "modal",
}

export interface InnerOverlayContextInterface {
  title?: string;
  content?: string | React.ReactNode;
  status?: "success" | "error";
  data?: any;
}

export type ShowOverlayType = (
  type: OverlayType,
  theme?: OverlayTheme,
  context?: InnerOverlayContextInterface
) => void;

export interface OverlayContextInterface {
  type: OverlayType | null;
  theme: OverlayTheme | null;
  context: InnerOverlayContextInterface;
  show: ShowOverlayType;
  hide(): void;
}

/* tslint:disable:no-empty */
export const OverlayContext = React.createContext<OverlayContextInterface>({
  context: null,
  hide: () => {},
  show: type => {},
  theme: null,
  type: null,
});
/* tslint:enable:no-empty */

OverlayContext.displayName = "OverlayContext";
