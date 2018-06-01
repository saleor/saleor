import * as React from "react";
import { withStyles } from "material-ui/styles";

interface CategoryDetailsPageProps {}

const decorate = withStyles(theme => ({ root: {} }));
const CategoryDetailsPage = decorate<CategoryDetailsPageProps>(({ classes }) => <div />);
export default CategoryDetailsPage;
