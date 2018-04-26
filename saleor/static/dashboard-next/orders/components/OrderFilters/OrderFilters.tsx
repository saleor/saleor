import * as React from "react";
import { withStyles } from "material-ui/styles";

interface OrderFiltersProps {}

const decorate = withStyles(theme => ({ root: {} }));
const OrderFilters = decorate<OrderFiltersProps>(({ classes }) => <div />);
export default OrderFilters;
