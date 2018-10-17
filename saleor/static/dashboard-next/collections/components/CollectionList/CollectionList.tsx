import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

interface CollectionListProps {}

const decorate = withStyles(theme => ({ root: {} }));
const CollectionList = decorate<CollectionListProps>(({ classes }) => <div />);
CollectionList.displayName = "CollectionList";
export default CollectionList;
