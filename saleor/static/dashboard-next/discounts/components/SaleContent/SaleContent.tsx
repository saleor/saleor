import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

export interface SaleContentProps {}

const decorate = withStyles(theme => ({ root: {} }));
const SaleContent = decorate<SaleContentProps>(({ classes }) => <div />);
SaleContent.displayName = "SaleContent";
export default SaleContent;
