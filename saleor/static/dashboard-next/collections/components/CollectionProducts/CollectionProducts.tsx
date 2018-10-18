import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

export interface CollectionProductsProps {}

const decorate = withStyles(theme => ({ root: {} }));
const CollectionProducts = decorate<CollectionProductsProps>(({ classes }) => <div />);
CollectionProducts.displayName = "CollectionProducts";
export default CollectionProducts;
