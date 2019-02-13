import { ContentState } from "draft-js";
import * as React from "react";

interface LinkProps {
  children: React.ReactNode;
  contentState: ContentState;
  entityKey: string;
}

const Link: React.StatelessComponent<LinkProps> = ({
  children,
  contentState,
  entityKey
}) => <a href={contentState.getEntity(entityKey).getData().href}>{children}</a>;
export default Link;
