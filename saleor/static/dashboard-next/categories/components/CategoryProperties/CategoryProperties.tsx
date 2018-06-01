import * as React from "react";
import { withStyles } from "material-ui/styles";

interface CategoryPropertiesProps {}

const decorate = withStyles(theme => ({ root: {} }));
const CategoryProperties = decorate<CategoryPropertiesProps>(({ classes }) => <div />);
export default CategoryProperties;
