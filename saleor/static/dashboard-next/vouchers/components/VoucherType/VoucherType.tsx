import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

interface VoucherTypeProps {}

const decorate = withStyles(theme => ({ root: {} }));
const VoucherType = decorate<VoucherTypeProps>(({ classes }) => <div />);
VoucherType.displayName = "VoucherType";
export default VoucherType;
