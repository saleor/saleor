import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

export interface SaleCollectionsProps {}

const decorate = withStyles(theme => ({ root: {} }));
const SaleCollections = decorate<SaleCollectionsProps>(({ classes }) => <div />);
SaleCollections.displayName = "SaleCollections";
export default SaleCollections;
