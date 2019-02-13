import * as React from "react";

interface LinkProps {
  children: React.ReactNode;
}

const Link: React.StatelessComponent<LinkProps> = ({ children }) => (
  <a>{children}</a>
);
export default Link;
