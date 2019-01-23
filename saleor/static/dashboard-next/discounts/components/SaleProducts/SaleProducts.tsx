import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

export interface SaleProductsProps {}

const decorate = withStyles(theme => ({ root: {} }));
const SaleProducts = decorate<SaleProductsProps>(({ classes }) => <div />);
SaleProducts.displayName = "SaleProducts";
export default SaleProducts;
