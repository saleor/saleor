import { ContentState } from "draft-js";
import * as React from "react";
import Link from "../Link";

interface LinkEntityProps {
  children: React.ReactNode;
  contentState: ContentState;
  entityKey: string;
}

const LinkEntity: React.StatelessComponent<LinkEntityProps> = ({
  children,
  contentState,
  entityKey
}) => (
  <Link href={contentState.getEntity(entityKey).getData().href}>
    {children}
  </Link>
);
export default LinkEntity;
