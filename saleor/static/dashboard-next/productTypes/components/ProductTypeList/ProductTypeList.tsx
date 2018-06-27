import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

interface ProductTypeListProps {}

const decorate = withStyles(theme => ({ root: {} }));
const ProductTypeList = decorate<ProductTypeListProps>(({ classes }) => <div />);
ProductTypeList.displayName = "ProductTypeList";
export default ProductTypeList;
