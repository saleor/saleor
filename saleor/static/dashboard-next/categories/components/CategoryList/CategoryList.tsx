import * as React from "react";
import { withStyles } from "material-ui/styles";

interface CategoryListProps {}

const decorate = withStyles(theme => ({ root: {} }));
const CategoryList = decorate<CategoryListProps>(({ classes }) => <div />);
export default CategoryList;
