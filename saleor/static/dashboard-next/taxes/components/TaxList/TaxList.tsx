import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

export interface TaxListProps {}

const decorate = withStyles(theme => ({ root: {} }));
const TaxList = decorate<TaxListProps>(({ classes }) => <div />);
TaxList.displayName = "TaxList";
export default TaxList;
