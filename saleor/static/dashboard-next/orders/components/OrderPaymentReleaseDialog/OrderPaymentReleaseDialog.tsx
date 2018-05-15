import * as React from "react";
import { withStyles } from "material-ui/styles";

interface OrderPaymentReleaseDialogProps {}

const decorate = withStyles(theme => ({ root: {} }));
const OrderPaymentReleaseDialog = decorate<OrderPaymentReleaseDialogProps>(({ classes }) => <div />);
export default OrderPaymentReleaseDialog;
