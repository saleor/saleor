import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

interface VoucherPropertiesProps {}

const decorate = withStyles(theme => ({ root: {} }));
const VoucherProperties = decorate<VoucherPropertiesProps>(({ classes }) => <div />);
VoucherProperties.displayName = "VoucherProperties";
export default VoucherProperties;
