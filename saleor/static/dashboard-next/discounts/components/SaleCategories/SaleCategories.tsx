import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

export interface SaleCategoriesProps {}

const decorate = withStyles(theme => ({ root: {} }));
const SaleCategories = decorate<SaleCategoriesProps>(({ classes }) => <div />);
SaleCategories.displayName = "SaleCategories";
export default SaleCategories;
